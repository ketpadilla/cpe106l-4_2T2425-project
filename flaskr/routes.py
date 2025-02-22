from flask import Flask, session, url_for, redirect, render_template, request, redirect
from markupsafe import escape
from .user.models import User

def configure_routes(app, WEB_NAME):
  @app.route("/")
  def index(page_title = WEB_NAME):
      return render_template('index.html', title = page_title)

  @app.route("/sign-in/", methods=['GET', 'POST'])
  def login():
    if request.method == 'POST':
      session['user'] = "test_user"
      return redirect(url_for('profile', username=session['user']))
    return render_template('sign-in.html', title="Sign In") 

  @app.route("/sign-up/", methods=['GET', 'POST'])
  def register():
    if request.method == 'POST':
      User().sign_up()
      return redirect(url_for('index'))
    return render_template('sign-up.html', title="Sign Up")

  @app.route("/sign-out/")
  def logout():
    session.pop('user', None)
    return redirect(url_for('sign-out'))
    
  @app.route("/user/<username>/")
  def profile(username):
    return f"{escape(username)}\'s Profile"

  @app.errorhandler(404)
  def page_not_found(error):
    return render_template('page-not-found.html', title = '404'), 404