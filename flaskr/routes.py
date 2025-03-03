from flask import Flask, session, url_for, redirect, render_template, request, redirect, jsonify
from markupsafe import escape
from passlib.hash import pbkdf2_sha256
from .user.models import *
from .utils import login_required 
from .app import db, food_api

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

  @app.route("/api/add-favorite", methods=['POST'])
  def add_favorite():
    #TODO
    pass

  @app.route("/api/add-daily-intake", methods=['POST'])
  def add_daily_intake():
    #TODO
    pass

  @app.route("/calories/")
  @login_required
  def calories():
    return render_template('calories.html', title='Daily Calorie Intake')
    
  @app.route("/history/")
  @login_required
  def history():
    return render_template('history.html', title='View History')
  
  @app.errorhandler(404)
  def page_not_found(error):
    return render_template('page-not-found.html', title = '404'), 404