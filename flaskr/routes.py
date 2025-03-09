from flask import session, url_for, redirect, render_template, request, redirect, jsonify
from .app import db, food_api
from .user.models import User
from .user.intake_api import IntakeAPI
from .user.local_api import LocalAPI
from .utils import login_required

from passlib.hash import pbkdf2_sha256

local_api = LocalAPI(db, food_api)
intake_api = IntakeAPI(db)

def configure_routes(app, WEB_NAME):
  """
    Landing Page
  """
  @app.route("/")
  def index(page_title = WEB_NAME):
    return render_template('index.html', title=page_title)
  
  """
    BMI Calculator
  """
  @app.route("/bmi-calculator/")
  def bmi_calculator():
    return render_template('bmi.html', title='BMI Calculator')
  
  """
    User Management
  """
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
    
  """
    Search Food
  """
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

  """
    Favorites
  """
  @app.route('/api/add-favorite', methods=['POST'])
  @login_required
  def add_favorite():
    data = request.get_json()
    fdc_id = data.get('fdcId')

    if not fdc_id:
      return jsonify({"error": "Missing food ID"}), 400

    email = session['user']['email']
    return User().add_to_favorites(email, fdc_id)
  
  @app.route('/api/remove-favorite', methods=['POST'])
  @login_required
  def remove_favorite():
    data = request.get_json()
    fdc_id = data.get('fdcId')
    
    if not fdc_id:
      return jsonify({"error": "Missing food ID"}), 400
        
    email = session['user']['email']
    return User().remove_from_favorites(email, fdc_id)

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
  
  """
    Daily Record
  """
  @app.route("/calories/")
  @login_required
  def calories():
    return render_template('calories.html', title='Daily Calorie Intake')
  
  @app.route('/api/add-daily-intake', methods=['POST'])
  @login_required
  def add_daily_intake():
    data = request.json
    return intake_api.add_daily_intake(session["user"]["email"], data)
  
  @app.route('/api/update-daily-intake/', methods=['POST'])
  @login_required
  def update_daily_intake():
    data = request.json
    return intake_api.update_daily_intake(session["user"]["email"], data)

  @app.route('/api/remove-daily-intake', methods=['POST'])
  @login_required
  def remove_daily_intake():
    return intake_api.remove_daily_intake(session["user"]["email"])

  @app.route("/api/user-calories", methods=["GET"])
  @login_required
  def user_calories():
    return intake_api.user_calories(session["user"]["email"])
  
  @app.route('/api/get-daily-intake', methods=['GET'])
  @login_required
  def get_daily_intake():
    return intake_api.get_daily_intake(session["user"]["email"])

  """
    Intake History
  """
  @app.route("/history/")
  @login_required
  def history():
    return render_template('history.html', title='View History')
  
  #TODO: to implement
  """
    Error Handling Pages
  """
  @app.errorhandler(404)
  def page_not_found(error):
    return render_template('page-not-found.html', title = '404'), 404