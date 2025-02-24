from flask import Flask, session, url_for, redirect, render_template, request, redirect, jsonify
from markupsafe import escape
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

  # @app.route("/api/search-food/", methods=['GET'])
  # def api_search_food():
  #   query = request.args.get('query', '').strip()

  #   # If the search is empty, return an empty list immediately
  #   if not query:
  #     return jsonify([])

  #   url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={food_api}&query={query}"

  #   try:
  #     response = requests.get(url)

  #     if response.status_code == 200:
  #       data = response.json()
  #       result_list = data.get('foods', [])  # Extract 'foods' from API response

  #       # Get rate limit details from headers
  #       rate_limit = response.headers.get('X-RateLimit-Limit', 'Unknown')
  #       rate_remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')

  #       # Print rate limit details to console
  #       print(f"Rate Limit: {rate_limit}, Remaining: {rate_remaining}")
  #       return jsonify(result_list)
  #     else:
  #       print(f"Failed to retrieve data. Status code: {response.status_code}")
  #       return jsonify([])  # Return empty list on failure
  #   except requests.RequestException as e:
  #     print(f"Request failed: {e}")
  #     return jsonify([])  # Return empty list if request fails

  @app.route("/api/search-food/", methods=['GET'])
  def api_search_food():
    query = request.args.get('query', '').strip()

    if not query:  # If no search term, return an empty list
      return jsonify([])

    regex_query = re.compile(f'^{re.escape(query)}', re.IGNORECASE)
    branded_results = db["branded-foods"].find({"Description": regex_query})
    survey_results = db["survey-foods"].find({"Description": regex_query})

    result_list = [{'id': str(result['_id']), 'name': result['Description']} for result in branded_results]
    result_list.extend([{'id': str(result['_id']), 'name': result['Description']} for result in survey_results])

    return jsonify(result_list)

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