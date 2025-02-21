from flask import Flask, render_template, session, redirect, request, url_for
from functools import wraps
import pymongo
from .user.models import User 

app = Flask(__name__)
WEB_NAME = 'Trackabite'

client = pymongo.MongoClient('localhost', 27017)
db = client.user_login_system

@app.route("/")
def index(page_title=WEB_NAME):
    return render_template('index.html', title=page_title)

@app.route("/login", methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    session['user'] = "test_user"
    return redirect(url_for('profile', username=session['user']))
  return render_template('login.html', title="Login")

@app.route("/register", methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    return User().signup()
  return render_template('register.html', title="Register")

@app.route("/logout")
def logout():
  session.pop('user', None)
  return redirect(url_for('login'))

@app.route("/user/<username>")
def profile(username):
  return f"{escape(username)}'s Profile"

@app.errorhandler(404)
def page_not_found(error):
  return render_template('page_not_found.html', title='404'), 404

if __name__ == "__main__":
  app.run(debug=True)