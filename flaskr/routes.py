from flask import session, url_for, redirect, render_template, request, redirect, jsonify
from .app import db, food_api
from .user.models import User
from .user.intake_api import IntakeAPI
from .user.local_api import LocalAPI
from .utils import login_required

from passlib.hash import pbkdf2_sha256

local_api = LocalAPI(db, food_api)
intake_api = IntakeAPI(db)

def configure_routes(app, WEB_NAME):
  """Configure all routes for the Flask application.

  This function sets up all the routes for the application, including user management,
  food search, favorites, daily calorie tracking, and history.

  Args:
    app (Flask): The Flask application instance.
    WEB_NAME (str): The name of the web application, used for page titles.
  """

  """
    Landing Page
  """
  @app.route("/")
  def index(page_title = WEB_NAME):
    """Render the landing page.

    Args:
      page_title (str): The title of the page, defaults to the web application name.

    Returns:
      str: Rendered HTML template for the landing page.
    """
    return render_template('index.html', title=page_title)
  
  """
    BMI Calculator
  """
  @app.route("/bmi-calculator/")
  def bmi_calculator():
    """Render the BMI calculator page.

    Returns:
      str: Rendered HTML template for the BMI calculator page.
    """
    return render_template('bmi.html', title='BMI Calculator')
  
  """
    User Management
  """
  @app.route("/sign-in/", methods=['GET', 'POST'])
  def login():
    """Handle user login.

    If the request method is POST, attempt to log the user in. If successful,
    redirect to the user's profile page. Otherwise, display an error message.

    Returns:
      str: Rendered HTML template for the sign-in page or a redirect to the profile page.
    """
    if request.method == 'POST':
      result = User().sign_in()
      if result[1] == 401:
        return render_template('sign-in.html', title="Sign In", error=result[0]['error'])
      return redirect(url_for('profile', username=session['user']['name']))
    return render_template('sign-in.html', title="Sign In")

  @app.route("/sign-up/", methods=['GET', 'POST'])
  def register():
    """Handle user registration.

    If the request method is POST, attempt to register the user. If successful,
    redirect to the landing page. Otherwise, display an error message.

    Returns:
      str: Rendered HTML template for the sign-up page or a redirect to the landing page.
    """
    if request.method == 'POST':
      result = User().sign_up()
      if result[1] == 400:
        return render_template('sign-up.html', title="Sign Up", error=result[0]['error'])
      return redirect(url_for('index'))
    return render_template('sign-up.html', title="Sign Up")
  
  @app.route("/forgot-password/", methods = ['GET', 'POST'])
  def forgot_password():
    """Handle password reset requests.

    If the request method is POST, validate the email and new password. If valid,
    update the user's password and display a success message.

    Returns:
      str: Rendered HTML template for the forgot password page.
    """
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
    """Handle user logout.

    Logs the user out and redirects to the landing page.

    Returns:
      str: Redirect to the landing page.
    """
    User().sign_out()
    return redirect(url_for('index'))
    
  @app.route("/user/<username>/")
  @login_required
  def profile(username):
    """Render the user's profile page.

    Args:
      username (str): The username of the profile to display.

    Returns:
      str: Rendered HTML template for the user's profile page.
    """
    return render_template('user.html', title=f"{username}'s Profile", username=username)

  @app.route("/update-profile/", methods=['POST'])
  @login_required
  def update_profile():
    """Update the user's profile information.

    Returns:
      str: Redirect to the user's profile page.
    """
    User().update_profile()
    return redirect(url_for('profile', username=session['user']['name']))

  @app.route("/update-calorie-intake/", methods=['POST'])
  @login_required
  def update_calories():
    """Update the user's recommended calorie intake.

    Returns:
      str: JSON response indicating success or failure.
    """
    data = request.get_json()
    recommended_calorie_intake = data.get('recommended_calorie_intake')

    if not recommended_calorie_intake:
      return jsonify({"error": "Recommended calorie intake is required"}), 400

    result = User().update_calorie_intake(session['user']['email'], recommended_calorie_intake)
    
    if result:
      return jsonify({"message": "Calorie intake updated successfully", "recommended_calorie_intake": recommended_calorie_intake}), 200
    return jsonify({"error": "Failed to update calorie intake"}), 500
    
  """
    Search Food
  """
  @app.route("/search-food/", methods=['GET'])
  def search_food():
    """Render the food search page.

    Returns:
      str: Rendered HTML template for the food search page.
    """
    return render_template('food.html', title='Search Food')

  @app.route("/api/search-food/", methods=['GET'])
  def api_search_food():
    """Search for food items in the database.

    Returns:
      str: JSON response containing search results.
    """
    return local_api.search_database()

  @app.route("/api/food-details/<fdc_id>", methods=['GET'])
  def food_details(fdc_id):
    """Get details for a specific food item.

    Args:
      fdc_id (str): The FDC ID of the food item.

    Returns:
      str: JSON response containing food details.
    """
    return local_api.food_details(fdc_id)

  @app.route("/api/add-custom-food", methods =['POST'])
  def add_custom_food():
    """Add a custom food item to the database.

    Returns:
      str: JSON response indicating success or failure.
    """
    data = request.get_json()
    food_name = data.get('foodName')
    serving_size = data.get('servingSize')
    calories = float(data.get('calories'))
    brand_owner = data.get('brandOwner')
    custom_food_category = data.get('customFoodCategory')
    ingredients = data.get('ingredients')

    response, status = local_api.add_custom_food(food_name, calories, serving_size, brand_owner, custom_food_category, ingredients)
    return jsonify(response), status

  """
    Favorites
  """
  @app.route('/api/add-favorite', methods=['POST'])
  @login_required
  def add_favorite():
    """Add a food item to the user's favorites.

    Returns:
      str: JSON response indicating success or failure.
    """
    data = request.get_json()
    fdc_id = data.get('fdcId')

    if not fdc_id:
      return jsonify({"error": "Missing food ID"}), 400

    email = session['user']['email']
    return User().add_to_favorites(email, fdc_id)
  
  @app.route('/api/remove-favorite', methods=['POST'])
  @login_required
  def remove_favorite():
    """Remove a food item from the user's favorites.

    Returns:
      str: JSON response indicating success or failure.
    """
    data = request.get_json()
    fdc_id = data.get('fdcId')
    
    if not fdc_id:
      return jsonify({"error": "Missing food ID"}), 400
        
    email = session['user']['email']
    return User().remove_from_favorites(email, fdc_id)

  @app.route('/api/get-favorites', methods=['GET'])
  @login_required
  def get_favorites():
    """Get the user's favorite food items.

    Returns:
      str: JSON response containing the user's favorites.
    """
    email = session['user']['email']
    user_doc = db.users.find_one({"email": email})
    if not user_doc:
      return jsonify({"favorites": []})
    
    favorites = user_doc.get("favorites", [])
    favorite_details = []
    
    for fdc_id in favorites:
      food = db.get_collection("branded-foods").find_one({"FDC ID": fdc_id})
      if not food:
        food = db.get_collection("survey-foods").find_one({"FDC ID": fdc_id})
      if not food:
        food = db.get_collection("custom-foods").find_one({"FDC ID": fdc_id})
          
      if food:
        favorite_details.append({
          'fdcId': fdc_id,
          'name': food.get('Description', '').title(),
          'calories': food.get('Calories', 'N/A'),
          'serving_size': food.get('Serving Size', 'N/A'),
          'brand': food.get('Brand Owner', '').title() if 'Brand Owner' in food else None
        })
    
    return jsonify({"favorites": favorite_details})
  
  """
    Daily Record
  """
  @app.route("/calories/")
  @login_required
  def calories():
    """Render the daily calorie intake page.

    Returns:
      str: Rendered HTML template for the daily calorie intake page.
    """
    return render_template('calories.html', title='Daily Calorie Intake')
  
  @app.route('/api/add-daily-intake', methods=['POST'])
  @login_required
  def add_daily_intake():
    """Add a daily intake record for the user.

    Returns:
      str: JSON response indicating success or failure.
    """
    data = request.json
    return intake_api.add_daily_intake(session["user"]["email"], data)
  
  @app.route('/api/update-daily-intake/', methods=['POST'])
  @login_required
  def update_daily_intake():
    """Update the user's daily intake record.

    Returns:
      str: JSON response indicating success or failure.
    """
    data = request.json
    return intake_api.update_daily_intake(session["user"]["email"], data)

  @app.route('/api/remove-daily-intake', methods=['POST'])
  @login_required
  def remove_daily_intake():
    """Remove the user's daily intake record.

    Returns:
      str: JSON response indicating success or failure.
    """
    return intake_api.remove_daily_intake(session["user"]["email"])

  @app.route("/api/user-calories", methods=["GET"])
  @login_required
  def user_calories():
    """Get the user's calorie intake data.

    Returns:
      str: JSON response containing the user's calorie intake data.
    """
    return intake_api.user_calories(session["user"]["email"])
  
  @app.route('/api/get-daily-intake', methods=['GET'])
  @login_required
  def get_daily_intake():
    """Get the user's daily intake data.

    Returns:
      str: JSON response containing the user's daily intake data.
    """
    return intake_api.get_daily_intake(session["user"]["email"])

  """
    Intake History
  """
  @app.route("/history/")
  @login_required
  def history():
    """Render the intake history page.

    Returns:
      str: Rendered HTML template for the intake history page.
    """
    return render_template('history.html', title='View History')
  
  @app.route('/api/get-history', methods=['GET'])
  @login_required
  def get_history():
    """Get the user's intake history.

    Returns:
      str: JSON response containing the user's intake history.
    """
    return intake_api.get_history(session["user"]["email"])

  @app.route('/api/get-record', methods=['GET'])
  @login_required
  def get_record():
    """Get a specific intake record for the user.

    Returns:
      str: JSON response containing the intake record.
    """
    date = request.args.get('date')
    if not date:
      return jsonify({"error": "Date parameter is required"}), 400

    return intake_api.get_record(session["user"]["email"], date)

  """
    Error Handling Pages
  """
  @app.errorhandler(404)
  def page_not_found(error):
    """Render the 404 error page.

    Args:
      error (Exception): The error object.

    Returns:
      str: Rendered HTML template for the 404 error page.
    """
    return render_template('page-not-found.html', title = '404'), 404