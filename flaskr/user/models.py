from flask import Flask, jsonify, request, session, redirect, url_for
from passlib.hash import pbkdf2_sha256
from bson import ObjectId
from ..app import db
from ..utils import login_required
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
    }

    current_data = db.users.find_one({"email": user['email']})
    if current_data == updated_data:
      print("No changes detected. Skipping update.")
      return jsonify({"message": "No changes detected."}), 200

    result = db.users.update_one({"email": user['email']}, {"$set": updated_data})
    print(f"Modified Count: {result.modified_count}")

    session["user"].update(updated_data)
    session.modified = True

    if updated_data["weight"] != current_data.get("weight") or updated_data["height"] != current_data.get("height"):
      return self.calculate_bmi()

    print("Profile updated successfully!", "success")
    return jsonify({"message": "Profile updated successfully"}), 200

