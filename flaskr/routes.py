from flask import Flask, session, url_for, redirect, render_template, request, redirect
from functools import wraps
from markupsafe import escape
from .user.models import User

def login_required(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else: 
      print('Not logged in. Returning to Home Page')
      return redirect('/')

  return wrap

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

  @app.route("/bmi-calculator/")
  def bmi_calculator():
    return render_template('bmi.html', title='BMI Calculator')
    
  @app.route("/search-food/")
  def search_food():
    return render_template('food.html', title='Search Food')
    
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