from flask import Flask, jsonify, request, session
from passlib.hash import pbkdf2_sha256
from bson import ObjectId
from ..app import db
from ..utils import login_required
import re
import requests

class User:
  def start_session(self, user):
    del user['password']
    session['logged_in'] = True
    session['user'] = user

    return jsonify(user), 200

  def sign_up(self):
    valid_object_id = str(ObjectId())
    weight = float(request.form.get('weight', 0))
    height = float(request.form.get('height', 0))
    bmi = weight / ((height / 100) ** 2) if weight > 0 and height > 0 else None

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
      "bmi": bmi
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
  def calculate_bmi(self):
    user = session.get('user', {})
    weight = float(user.get('weight', 0))
    height = float(user.get('height', 0))

    if weight <= 0 or height <= 0:
      return jsonify({"error": "Invalid weight or height"}), 400

    calculated_bmi = weight / ((height / 100) ** 2)
    current_bmi = user.get('bmi')

    if calculated_bmi == current_bmi:
      return jsonify({"message": "BMI unchanged"}), 200 

    user_id = user.get("_id")
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"bmi": calculated_bmi}})
    session['user']['bmi'] = calculated_bmi
    return jsonify({"bmi": calculated_bmi, "message": "BMI updated successfully"}), 200

  @login_required
  def update_profile(self):
    user = session.get("user", {})

    updated_data = {
      "name": request.form.get("name", ""),
      "email": request.form.get("email", ""),
      "sex": request.form.get("sex", ""),
      "dob": request.form.get("dob", ""),
      "weight": float(request.form.get("weight", 0) or 0),
      "height": float(request.form.get("height", 0) or 0),
      "activity_level": request.form.get("activity_level", ""),
      "recommended_calorie_intake": float(request.form.get("daily_calorie_intake", 0) or 0)
    }

    current_data = db.users.find_one({"email": user['email']})
    if current_data == updated_data:
      print("No changes detected. Skipping update.")
      return jsonify({"message": "No changes detected."}), 200

    # update the bmi in mongodb
    if (updated_data["weight"] != current_data.get("weight") or
        updated_data["height"] != current_data.get("height")):
      weight = updated_data["weight"]
      height = updated_data["height"]
      bmi = weight / ((height / 100) ** 2) if weight > 0 and height > 0 else None
      updated_data["bmi"] = bmi

    result = db.users.update_one({"email": user["email"]}, {"$set": updated_data})
    print(f"Modified Count: {result.modified_count}")

    session["user"].update(updated_data)
    session.modified = True

    print("Profile updated successfully!", "success")
    return jsonify({
      "message": "Profile updated successfully",
      "bmi": session["user"].get("bmi", None)
    }), 200

class LocalAPI:
  def __init__(self, db, food_api):
    self.db = db
    self.food_api = food_api

  def search_database(self):
    query = request.args.get('query', '').strip()
    if not query:
      return jsonify([])

    regex_query = re.compile(f'^{re.escape(query)}', re.IGNORECASE)
    branded_results = self.db["branded-foods"].find({"Description": regex_query})
    survey_results = self.db["survey-foods"].find({"Description": regex_query})

    return jsonify(self._format_db_search_results(branded_results, survey_results))

  def food_details(self, fdc_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={self.food_api}"

    try:
      response = requests.get(url)
      if response.status_code == 200:
        data = response.json()
        return jsonify(self._format_usda_food_details(data))
      else:
        return jsonify({'error': 'Food details not found'}), 404
    except requests.RequestException as e:
      return jsonify({'error': f'Request failed: {e}'}), 500

  def _format_db_search_results(self, branded_results, survey_results):
    return [
      {
        'id': str(result['_id']),
        'name': result['Description'].title(),
        'calories': result.get('Calories', 'N/A'),
        'serving_size': result.get('Serving Size', 'N/A'),
        'brand': result.get('Brand Owner', 'N/A').title() if 'Brand Owner' in result else None,
        'fdcId': result.get('FDC ID', None)
      }
      for result in list(branded_results) + list(survey_results)
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
