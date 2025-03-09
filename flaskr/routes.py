from flask import session, url_for, redirect, render_template, request, redirect, jsonify
from passlib.hash import pbkdf2_sha256
from .user.models import *
from .utils import login_required 
from .app import db, food_api
from passlib.hash import pbkdf2_sha256

from datetime import datetime
from flask import jsonify, session
from bson.objectid import ObjectId

local_api = LocalAPI(db, food_api)

def configure_routes(app, WEB_NAME):
  @app.route("/")
  def index(page_title = WEB_NAME):
    return render_template('index.html', title=page_title)
  
  @app.route("/update-calorie-intake/", methods=['POST'])
  @login_required
  def update_calories():
    data = request.get_json()
    recommended_calorie_intake = data.get('recommended_calorie_intake')

    if not recommended_calorie_intake:
      return jsonify({"error": "Recommended calorie intake is required"}), 400

    result = User().update_calorie_intake(session['user']['email'], recommended_calorie_intake)
    
    if result:
      return jsonify({"message": "Calorie intake updated successfully", "recommended_calorie_intake": recommended_calorie_intake}), 200
    return jsonify({"error": "Failed to update calorie intake"}), 500

  @app.route("/sign-in/", methods=['GET', 'POST'])
  def login():
    if request.method == 'POST':
      result = User().sign_in()
      if result[1] == 401:
        return render_template('sign-in.html', title="Sign In", error=result[0]['error'])
      return redirect(url_for('profile', username=session['user']['name']))
    return render_template('sign-in.html', title="Sign In")

  @app.route("/sign-up/", methods=['GET', 'POST'])
  def register():
    if request.method == 'POST':
      result = User().sign_up()
      if result[1] == 400:
        return render_template('sign-up.html', title="Sign Up", error=result[0]['error'])
      return redirect(url_for('index'))
    return render_template('sign-up.html', title="Sign Up")
  
  @app.route("/forgot-password/", methods = ['GET', 'POST'])
  def forgot_password():
    if request.method == 'POST':
      email = request.form['email']
      new_password = request.form['new_password']
      confirm_password = request.form['confirm_password']

      if new_password != confirm_password:
        return render_template('forgot-password.html', title='Forgot Password', error='Passwords do not match')
      
      user = User().find_by_email(email)
      if not user:
        return render_template('forgot-password.html', title='Forgot Password', error='Email not found')
      
      if pbkdf2_sha256.verify(new_password, user['password']):
        return render_template('forgot-password.html', title='Forgot Password', error='Password matches your previous')
      
      User().update_password(email, new_password)
      return render_template('forgot-password.html', title='Forgot Password', message='Password has been reset successfully')
    
    return render_template('forgot-password.html', title='Forgot Password')

  @app.route("/sign-out/")
  def logout():
    User().sign_out()
    return redirect(url_for('index'))
    
  @app.route("/user/<username>/")
  @login_required
  def profile(username):
    return render_template('user.html', title=f"{username}'s Profile", username=username)

  @app.route("/update-profile/", methods=['POST'])
  @login_required
  def update_profile():
    User().update_profile()
    return redirect(url_for('profile', username=session['user']['name']))

  @app.route("/bmi-calculator/")
  def bmi_calculator():
    return render_template('bmi.html', title='BMI Calculator')
    
  @app.route("/search-food/", methods=['GET'])
  def search_food():
    return render_template('food.html', title='Search Food')

  @app.route("/api/search-food/", methods=['GET'])
  def api_search_food():
    return local_api.search_database()

  @app.route("/api/food-details/<fdc_id>", methods=['GET'])
  def food_details(fdc_id):
    return local_api.food_details(fdc_id)

  @app.route("/api/add-custom-food", methods =['POST'])
  def add_custom_food():
    data = request.get_json()
    food_name = data.get('foodName')
    serving_size = data.get('servingSize')
    calories = data.get('calories')
    brand_owner = data.get('brandOwner')
    custom_food_category = data.get('customFoodCategory')
    ingredients = data.get('ingredients')

    response, status = local_api.add_custom_food(food_name, calories, serving_size, brand_owner, custom_food_category, ingredients)
    return jsonify(response), status

  @app.route('/api/add-favorite', methods=['POST'])
  @login_required
  def add_favorite():
    data = request.get_json()
    fdc_id = data.get('fdcId')

    if not fdc_id:
      return jsonify({"error": "Missing food ID"}), 400

    email = session['user']['email']
    return User().add_to_favorites(email, fdc_id)

  @app.route('/api/add-daily-intake', methods=['POST'])
  @login_required
  def add_daily_intake():
    user_email = session["user"]["email"]
    user = db.users.find_one({"email": user_email}, {"_id": 1})

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    data = request.json
    fdc_id = data.get("fdcId")

    if not fdc_id:
        return jsonify({"error": "Missing food ID"}), 400

    # Retrieve food details from multiple collections
    food = db.get_collection("branded-foods").find_one({"FDC ID": fdc_id}) or \
           db.get_collection("survey-foods").find_one({"FDC ID": fdc_id}) or \
           db.get_collection("custom-foods").find_one({"FDC ID": fdc_id})

    if not food:
        return jsonify({"error": "Food not found"}), 404

    # If calories are missing, assign a default value or insert into DB
    if "Calories" not in food or not isinstance(food["Calories"], (int, float)):
        estimated_calories = 100  # Default value (can be adjusted)
        db.get_collection("custom-foods").update_one(
            {"FDC ID": fdc_id}, {"$set": {"Calories": estimated_calories}}, upsert=True
        )
        calories_per_serving = estimated_calories
    else:
        calories_per_serving = int(food["Calories"])

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if daily_record:
        existing_food = next((item for item in daily_record["consumed"] if item["fdcId"] == fdc_id), None)

        if existing_food:
            db["intake-daily"].update_one(
                {"_id": daily_record["_id"], "consumed.fdcId": fdc_id},
                {
                    "$inc": {
                        "consumed.$.servings": 1,
                        "total_calories": calories_per_serving
                    }
                }
            )
        else:
            db["intake-daily"].update_one(
                {"_id": daily_record["_id"]},
                {
                    "$push": {"consumed": {"fdcId": fdc_id, "servings": 1, "calories": calories_per_serving}},
                    "$inc": {"total_calories": calories_per_serving}
                }
            )
    else:
        db["intake-daily"].insert_one({
            "user_id": user_id,
            "date": today,
            "consumed": [{"fdcId": fdc_id, "servings": 1, "calories": calories_per_serving}],
            "total_calories": calories_per_serving
        })

    return jsonify({"message": "Food added successfully!", "calories_added": calories_per_serving})


  @app.route('/api/update-daily-intake/', methods=['POST'])
  @login_required
  def update_daily_intake():
    user_email = session["user"]["email"]
    user = db.users.find_one({"email": user_email}, {"_id": 1})

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    data = request.json
    fdc_id = int(data.get("fdcId"))
    new_servings = data.get("servings")

    if not fdc_id or not isinstance(new_servings, int) or new_servings < 1:
        return jsonify({"error": "Invalid food ID or servings count"}), 400

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
        return jsonify({"error": "Daily intake record not found"}), 404

    # Find the food item in the consumed array
    existing_food = None
    for item in daily_record["consumed"]:
        if item["fdcId"] == fdc_id:
            existing_food = item  # Assign the entire item, not just fdc_id
            break

    if not existing_food:
        return jsonify({"error": "Food item not found"}), 404

    # Update the servings for the specific food item
    existing_food["servings"] = new_servings

    # Recalculate total_calories by summing up calories * servings for all items
    total_calories = 0
    for item in daily_record["consumed"]:
        food = db.get_collection("branded-foods").find_one({"FDC ID": item["fdcId"]}) or \
               db.get_collection("survey-foods").find_one({"FDC ID": item["fdcId"]}) or \
               db.get_collection("custom-foods").find_one({"FDC ID": item["fdcId"]})

        if food and "Calories" in food:
            total_calories += int(food["Calories"]) * item["servings"]

    # Update the daily record with the new total_calories
    db["intake-daily"].update_one(
        {"_id": daily_record["_id"]},
        {
            "$set": {
                "consumed": daily_record["consumed"],
                "total_calories": total_calories
            }
        }
    )

    # Fetch the updated daily record
    updated_record = db["intake-daily"].find_one({"_id": daily_record["_id"]})

    return jsonify({
        "message": "Servings updated successfully!",
        "new_total_calories": updated_record["total_calories"],
        "recommended_calories": user.get("recommended_calorie_intake", 2000),
        "consumed": updated_record.get("consumed", [])
    })

  @app.route('/api/remove-daily-intake', methods=['POST'])
  @login_required
  def remove_daily_intake():
    user_email = session["user"]["email"]
    user = db.users.find_one({"email": user_email}, {"_id": 1})

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    data = request.json
    fdc_id = int(data.get("fdcId"))

    if not fdc_id:
        return jsonify({"error": "Invalid food ID"}), 400

    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record:
        return jsonify({"error": "Daily intake record not found"}), 404

    # Find the food item in the consumed array
    existing_food = next((item for item in daily_record["consumed"] if item["fdcId"] == fdc_id), None)

    if not existing_food:
        return jsonify({"error": "Food item not found"}), 404

    # Remove the item from the consumed list
    db["intake-daily"].update_one(
        {"_id": daily_record["_id"]},
        {"$pull": {"consumed": {"fdcId": fdc_id}}}
    )

    # Recalculate total calories
    total_calories = sum(item["calories"] * item["servings"] for item in daily_record["consumed"] if item["fdcId"] != fdc_id)

    # Update the total_calories field
    db["intake-daily"].update_one(
        {"_id": daily_record["_id"]},
        {"$set": {"total_calories": total_calories}}
    )

    return jsonify({
        "message": "Food item removed successfully!",
        "new_total_calories": total_calories
    })


  @app.route('/api/remove-favorite', methods=['POST'])
  @login_required
  def remove_favorite():
    data = request.get_json()
    fdc_id = data.get('fdcId')
    
    if not fdc_id:
      return jsonify({"error": "Missing food ID"}), 400
        
    email = session['user']['email']
    return User().remove_from_favorites(email, fdc_id)

  @app.route("/calories/")
  @login_required
  def calories():
    # TODO
    return render_template('calories.html', title='Daily Calorie Intake')
  
  @app.route("/api/user-calories", methods=["GET"])
  @login_required
  def user_calories():
      user_email = session["user"]["email"]
      user = db.users.find_one({"email": user_email}, {"_id": 1, "recommended_calorie_intake": 1})
      
      if not user:
          return jsonify({"error": "User not found"}), 404

      user_id = user["_id"]
      recommended_calories = user.get("recommended_calorie_intake", 2000)

      # Find today's record
      today = datetime.utcnow().strftime("%Y-%m-%d")
      daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

      if not daily_record:
          return jsonify({
              "recommended_calories": recommended_calories,
              "consumed": [],
              "total_calories": 0,
          })

      return jsonify({
          "recommended_calories": recommended_calories,
          "consumed": daily_record.get("consumed", []),
          "total_calories": daily_record.get("total_calories", 0),
    })
  
  @app.route('/api/get-daily-intake', methods=['GET'])
  @login_required
  def get_daily_intake():
    user_email = session["user"]["email"]
    user = db.users.find_one({"email": user_email}, {"_id": 1})


    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["_id"]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    daily_record = db["intake-daily"].find_one({"user_id": user_id, "date": today})

    if not daily_record or not daily_record.get("consumed"):
        return jsonify({"foods": []})

    food_entries = []
    for item in daily_record["consumed"]:
        fdc_id = item["fdcId"]
        servings = item["servings"]

        food = db.get_collection("branded-foods").find_one({"FDC ID": fdc_id}) or \
               db.get_collection("survey-foods").find_one({"FDC ID": fdc_id}) or \
               db.get_collection("custom-foods").find_one({"FDC ID": fdc_id})

        if food:
            food_entries.append({
                "fdcId": fdc_id,
                "name": food.get("Description", "Unknown").title(),
                "calories": int(food.get("Calories", 0)),
                "servings": servings,
                "serving_size": food.get("Serving Size", "N/A"),
                "brand": food.get("Brand Owner", "").title() if "Brand Owner" in food else None
            })

    for food in food_entries:
      print(food)
    return jsonify({"foods": food_entries})

  @app.route("/history/")
  @login_required
  def history():
    return render_template('history.html', title='View History')
  
  @app.errorhandler(404)
  def page_not_found(error):
    return render_template('page-not-found.html', title = '404'), 404
  
  @app.route('/api/get-favorites', methods=['GET'])
  @login_required
  def get_favorites():
    email = session['user']['email']
    user_doc = db.users.find_one({"email": email})
    if not user_doc:
      return jsonify({"favorites": []})
    
    favorites = user_doc.get("favorites", [])
    favorite_details = []
    
    for fdc_id in favorites:
      food = db.get_collection("branded-foods").find_one({"FDC ID": fdc_id})
      if not food:
        food = db.get_collection("survey-foods").find_one({"FDC ID": fdc_id})
      if not food:
        food = db.get_collection("custom-foods").find_one({"FDC ID": fdc_id})
          
      if food:
        favorite_details.append({
          'fdcId': fdc_id,
          'name': food.get('Description', '').title(),
          'calories': food.get('Calories', 'N/A'),
          'serving_size': food.get('Serving Size', 'N/A'),
          'brand': food.get('Brand Owner', '').title() if 'Brand Owner' in food else None
        })
    
    return jsonify({"favorites": favorite_details})