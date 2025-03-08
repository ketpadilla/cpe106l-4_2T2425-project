from flask import jsonify, request, session
from passlib.hash import pbkdf2_sha256
from bson import ObjectId
from pymongo import ReturnDocument
import requests, time
from ..app import db
from ..utils import login_required

class User:
  def start_session(self, user):
    user_copy = user.copy() 
    user_copy.pop("password", None)
    session['logged_in'] = True
    session['user'] = user_copy
    return jsonify(user_copy), 200

  def sign_up(self):
    # TODO: to check for possible optimizations
    valid_object_id = str(ObjectId())
    weight = float(request.form.get('weight', 0))
    height = float(request.form.get('height', 0))

    user = {
      "_id": valid_object_id,
      "name": request.form.get('name'),
      "email": request.form.get('email'),
      "password": pbkdf2_sha256.hash(request.form.get('password')),
      "weight": weight,
      "height": height,
      "activity_level": request.form.get('activity_level'),
      "dob": request.form.get('dob'),
      "sex": request.form.get('sex'),
      "bmi": self._calculate_bmi(weight, height)
    }

    if db.users.find_one({"email": user['email']}):
      return {"error": "Email address already in use"}, 400

    if db.users.insert_one(user):
      return self.start_session(user)

    return {"error": "Signup failed"}, 400

  def sign_in(self):
    user = db.users.find_one({"email": request.form.get('email')})

    if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
      return self.start_session(user)

    return {"error": "Invalid email or password"}, 401

  def sign_out(self):
    session.clear()

  def find_by_email(self, email):
    return db.users.find_one({"email": email})

  def update_password(self, email, new_password):
    hashed_password = pbkdf2_sha256.hash(new_password)
    result = db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})
    return result.modified_count > 0

  @login_required
  def update_calorie_intake(self, email, recommended_calorie_intake):
    try:
      recommended_calorie_intake = float(recommended_calorie_intake)

      result = db.users.update_one(
        {"email": email}, 
        {"$set": {"recommended_calorie_intake": recommended_calorie_intake}}
      )

      if result.modified_count > 0:
        user = session.get("user", {})
        user["recommended_calorie_intake"] = recommended_calorie_intake
        session["user"] = user
        session.modified = True
        return True
      return False
    except Exception as e:
      print(f"Error updating calorie intake: {e}")
      return False

  @login_required
  def update_profile(self):
    user = session.get("user", {})
    email = user["email"]

    updated_data = {
      key: request.form.get(key, "").strip() for key in ["name", "email", "sex", "dob", "activity_level"]
    }

    updated_data["weight"] = float(request.form.get("weight", 0) or 0)
    updated_data["height"] = float(request.form.get("height", 0) or 0)
    # TODO: Update recommended daily calorie intake

    if "weight" in updated_data or "height" in updated_data:
      updated_data["bmi"] = self._calculate_bmi(updated_data["weight"], updated_data["height"])

    result = db.users.update_one({"email": email}, {"$set": updated_data})

    if result.modified_count > 0:
      session["user"].update(updated_data)
      session.modified = True
      return jsonify({"message": "Profile updated successfully", "bmi": session["user"].get("bmi")}), 200

    return jsonify({"message": "No changes detected."}), 200

  def _calculate_bmi(self, weight, height):
    return weight / ((height / 100) ** 2) if weight > 0 and height > 0 else None

  @login_required
  def add_to_favorites(self, email, fdc_id):
    user = db.users.find_one({"email": email})
    if not user:
      return jsonify({"error": "User not found"}), 404

    favorites = user.get("favorites", [])

    if fdc_id not in favorites:
      db.users.update_one(
        {"email": email},
        {"$push": {"favorites": fdc_id}}
      )

    return jsonify({"message": "Added to favorites successfully"}), 200
  
  @login_required
  def get_favorites(self, email):
    user = db.users.find_one({"email": email}, {"favorites": 1})
    if not user or "favorites" not in user:
      return jsonify({"favorites": []}), 200
    
    favorites_details = []
    for fdc_id in user["favorites"]:
      food = db.foods.find_one({"FDC ID": fdc_id})
      if food:
        favorites_details.append({
          "name": food.get("Description", "Unknown"),
          "calories": food.get("Calories", "N/A"),
          "serving_size": food.get("Serving Size", "N/A"),
          "brand": food.get("Brand Owner", None),
          "fdcId": fdc_id
          })
    
    return jsonify({"favorites": favorites_details}), 200

  @login_required
  def remove_from_favorites(self, email, fdc_id):
    result = db.users.update_one(
      {"email": email},
      {"$pull": {"favorites": fdc_id}}
    )
    
    if result.modified_count > 0:
      return jsonify({"message": "Removed from favorites successfully"}), 200
    return jsonify({"error": "Failed to remove from favorites or item not found"}), 400

class LocalAPI:
  def __init__(self, db, food_api):
    self.db = db
    self.food_api = food_api

  def atlas_search(self, collection, index_name, weight, query, page, limit):
    pipeline = [
        {
          "$search": {
            "index": index_name,
            "compound": {
              "should": [
                {
                  "phrase": { 
                    "query": query,
                    "path": "Description",
                    "slop": 0,
                  }
              },
              {
                  "text": {  
                    "query": query,
                    "path": "Description",
                    "score": {"boost": {"value": 20}}  
                  }
              },
              {
                  "text": { 
                    "query": query,
                    "path": "Description",
                    "fuzzy": {"maxEdits": 1, "prefixLength": 2},
                    "score": {"boost": {"value": 5}}
                  }
                }
              ]
            }
          }
        },
        {
          "$addFields": {
            "searchScore": {"$meta": "searchScore"},
            "adjustedScore": {"$multiply": [{"$meta": "searchScore"}, weight]}  
          }
        },
        {"$sort": {"adjustedScore": -1}},  
        {"$skip": (page - 1) * limit},
        {"$limit": limit}
    ]

    return list(self.db[collection].aggregate(pipeline))
  
  def search_database(self):
    query = request.args.get('query', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    if not query:
      return jsonify([])

    start_time = time.time()

    branded_count = self.db["branded-foods"].count_documents({})
    survey_count = self.db["survey-foods"].count_documents({})
    custom_count = self.db["custom-foods"].count_documents({})

    total_docs = branded_count + survey_count + custom_count
    branded_weight = total_docs / branded_count if branded_count else 1
    survey_weight = total_docs / survey_count if survey_count else 1
    custom_weight = total_docs / custom_count if custom_count else 1


    branded_results = self.atlas_search("branded-foods", "FoodDesc_BF", branded_weight, query, page, limit)
    survey_results = self.atlas_search("survey-foods", "FoodDesc_SF", survey_weight, query, page, limit)
    custom_results = self.atlas_search("custom-foods", "FoodDesc_CF", custom_weight, query, page, limit)

    all_results = branded_results + survey_results + custom_results
    all_results.sort(key=lambda x: x["adjustedScore"], reverse=True)

    search_time = time.time() - start_time
    print(f"\nSearch execution time: {search_time:.4f} seconds")

    return jsonify({
        "results": self._format_db_search_results(all_results),
        "has_more": len(all_results) >= limit
    })


  def food_details(self, fdc_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={self.food_api}"

    try:
      response = requests.get(url)
      response.raise_for_status()
      return jsonify(self._format_usda_food_details(response.json()))
    except requests.exceptions.HTTPError as e:
      return jsonify({'error': f'HTTP error: {e}'}), response.status_code
    except requests.exceptions.RequestException as e:
      return jsonify({'error': f'API request failed: {e}'}), 500

  def _format_db_search_results(self, *results):
    return [
      {
        'id': str(result['_id']),
        'name': result.get('Description', '').title(),
        'calories': result.get('Calories', 'N/A'),
        'serving_size': result.get('Serving Size', 'N/A'),
        'brand': result.get('Brand Owner', 'N/A').title() if 'Brand Owner' in result else None,
        'fdcId': result.get('FDC ID', None)
      }
      for result_set in results for result in result_set
    ]

  def _format_usda_food_details(self, data):
    food_type = data.get('dataType', 'N/A')

    nutrients = {
      nutrient.get('nutrient', {}).get('name'): nutrient.get('amount')
      for nutrient in data.get('foodNutrients', [])
      if nutrient.get('nutrient', {}).get('name') and nutrient.get('amount') is not None
    }

    serving_size = f"{data.get('servingSize', 'N/A')} {data.get('servingSizeUnit', 'N/A')}"

    attributes = {attr.get('name', 'Unknown'): attr.get('value', 'N/A') for attr in data.get('foodAttributes', [])}

    return {
      'name': data.get('description', 'N/A'),
      'calories': nutrients.get('Energy', 'N/A'),
      'protein': nutrients.get('Protein', 'N/A'),
      'carbs': nutrients.get('Carbohydrate, by difference', 'N/A'),
      'fats': nutrients.get('Total lipid (fat)', 'N/A'),
      'serving_size': serving_size,
      'attributes': attributes,
      'publication_date': data.get('publicationDate', 'N/A')
    }

  def add_custom_food(self, food_name, calories, serving_size=None, brand_owner=None, custom_food_category=None, ingredients=None):
    # TODO: To provide UI feedback
    if not food_name or not calories:
      return {"error": 'Missing required fields'}, 400

    existing_food = self.db["custom-foods"].find_one({
      "Description": food_name,
      "Brand Owner": brand_owner or "N/A",
      "Custom Food Category": custom_food_category or "N/A",
      "Calories": calories,
      "Ingredients": ingredients or "N/A",
      "Serving Size": serving_size or 100
    })
    if existing_food:
      return {"error": "Food item with the same data already exists"}, 400

    counter = self.db["counter"].find_one_and_update(
      {"_id": "fdc_id"},
      {"$inc": {"sequence_value": 1}},  
      return_document=ReturnDocument.AFTER,
      upsert=True  
    )

    fdc_id = counter["sequence_value"]

    new_food = {
      "_id": ObjectId(),
      "Food Class": "Custom",
      "FDC ID": fdc_id,
      "Description": food_name,
      "Brand Owner": brand_owner or "N/A",
      "Custom Food Category": custom_food_category or "N/A",
      "Calories": calories,
      "Ingredients": ingredients or "N/A",
      "Serving Size": serving_size or 100,
    }

    self.db["custom-foods"].insert_one(new_food)
    return {"message": "Food item added successfully!"}, 200