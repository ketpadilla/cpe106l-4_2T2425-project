from flask import Flask, jsonify, request, session
from passlib.hash import pbkdf2_sha256
from bson import ObjectId
from ..app import db

class User:
  def start_session(self, user):
    del user['password']
    session['logged_in'] = True
    session['user'] = user

    return jsonify(user), 200

  def sign_up(self):
    valid_object_id = str(ObjectId())
    user = {
      "_id": valid_object_id,
      "name": request.form.get('name'),
      "email": request.form.get('email'),
      "password": request.form.get('password'),
      "weight": request.form.get('weight'),
      "height": request.form.get('height'),
      "activity_level": request.form.get('activity_level'),
      "dob": request.form.get('dob'),
      "sex": request.form.get('sex')
    }

    user['password'] = pbkdf2_sha256.hash(user['password'])
    
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

  def calculate_bmi(self):
    return 