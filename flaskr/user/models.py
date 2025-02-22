from flask import Flask, jsonify

class User:
  def sign_up(self):
    user = {
      "_id": "",
      "name": "",
      "email": "",
      "password": ""
      # TODO: add more
    }

    return jsonify(user), 200