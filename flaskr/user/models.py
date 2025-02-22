from flask import Flask, jsonify, request
from passlib.hash import pbkdf2_sha256
import uuid

class User:
  def sign_up(self):
    user = {
      "_id": uuid.uuid4().hex,
      "name": request.form.get('name'),
      "email": request.form.get('email'),
      "password": request.form.get('password'),
      "weight": request.form.get('weight'),
      "height": request.form.get('height'),
      "activity_level": request.form.get('activity_level'),
      "dob": request.form.get('dob'),
      "sex": request.form.get('sex')
    }

    user['password'] = pbkdf2_sha256.encrypt(user['password'])
    print(user) 
    return jsonify(user), 200
