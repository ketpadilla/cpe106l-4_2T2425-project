from flask import Flask, session, url_for, redirect, render_template, request, redirect, jsonify
from markupsafe import escape
from passlib.hash import pbkdf2_sha256
from .user.models import User
from .utils import login_required 
from .app import db, food_api
import re 
import requests

def configure_routes(app, WEB_NAME):
  @app.route("/")
  def index(page_title = WEB_NAME):
      return render_template('index.html', title=page_title)

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
      query = request.args.get('query', '').strip()

      if not query:  
        return jsonify([])

      regex_query = re.compile(f'^{re.escape(query)}', re.IGNORECASE)
      branded_results = db["branded-foods"].find({"Description": regex_query})
      survey_results = db["survey-foods"].find({"Description": regex_query})

      result_list = []
      
      for result in list(branded_results) + list(survey_results):
        result_list.append({
          'id': str(result['_id']),
          'name': result['Description'].title(), 
          'calories': result.get('Calories', 'N/A'),
          'serving_size': result.get('Serving Size', 'N/A'),
          'brand': result.get('Brand Owner', 'N/A').title() if 'Brand Owner' in result else None,
          'fdcId': result.get('FDC ID', None) 
        })

      return jsonify(result_list)

  @app.route("/api/food-details/<fdc_id>", methods=['GET'])
  def food_details(fdc_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={food_api}"

    try:
      response = requests.get(url)
      if response.status_code == 200:
        data = response.json()
        food_type = data.get('dataType', 'N/A')

        nutrients = {}
        for nutrient in data.get('foodNutrients', []):
          nutrient_name = nutrient.get('nutrient', {}).get('name')
          nutrient_value = nutrient.get('amount') 
          if nutrient_name and nutrient_value is not None:
            nutrients[nutrient_name] = nutrient_value

        if food_type == "Survey (FNDDS)":
          serving_size = next(
            (f"{portion['portionDescription']} ({portion['gramWeight']} g)"
            for portion in data.get("foodPortions", [])
            if portion.get("portionDescription")), 
            "N/A"
          )
        else: 
          serving_size = f"{data.get('servingSize', 'N/A')} {data.get('servingSizeUnit', 'N/A')}"


        attributes = {}
        if 'foodAttributes' in data:
          for attr in data['foodAttributes']:
            attributes[attr.get('name', 'Unknown')] = attr.get('value', 'N/A')

        return jsonify({
          'name': data.get('description', 'N/A'),
          'food_class': data.get('foodClass', 'N/A'),
          'fdc_id': data.get('fdcId', 'N/A'),
          'food_code': data.get('foodCode', 'N/A'),
          'category': data.get('wweiaFoodCategory', {}).get('wweiaFoodCategoryDescription', 'N/A'),
          'calories': nutrients.get('Energy', 'N/A'),
          'protein': nutrients.get('Protein', 'N/A'),
          'carbs': nutrients.get('Carbohydrate, by difference', 'N/A'),
          'fats': nutrients.get('Total lipid (fat)', 'N/A'),
          'serving_size': serving_size,
          'attributes': attributes,
          'publication_date': data.get('publicationDate', 'N/A')
        })
      else:
        return jsonify({'error': 'Food details not found'}), 404
    except requests.RequestException as e:
      return jsonify({'error': f'Request failed: {e}'}), 500

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