from flask import jsonify, request, session
from passlib.hash import pbkdf2_sha256
from bson import ObjectId
from ..app import db

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

  def update_profile(self):
    user = session.get("user", {})
    email = user["email"]

    updated_data = {
      key: request.form.get(key, "").strip() for key in ["name", "email", "sex", "dob", "activity_level"]
    }

    updated_data["weight"] = float(request.form.get("weight", 0) or 0)
    updated_data["height"] = float(request.form.get("height", 0) or 0)

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

  def remove_from_favorites(self, email, fdc_id):
    result = db.users.update_one(
      {"email": email},
      {"$pull": {"favorites": fdc_id}}
    )
    
    if result.modified_count > 0:
      return jsonify({"message": "Removed from favorites successfully"}), 200
    return jsonify({"error": "Failed to remove from favorites or item not found"}), 400