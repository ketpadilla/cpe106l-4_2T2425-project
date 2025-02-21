from flask import Flask, session, url_for, redirect, render_template, request
from markupsafe import escape

app = Flask(__name__)
app.secret_key = 'your_secret_key' # TODO
WEB_NAME = 'Trackabite'

@app.route("/")
def index(page_title = WEB_NAME):
    return render_template('index.html', title = page_title)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = "test_user"
        return redirect(url_for('profile', username=session['user']))
    return render_template('login.html', title="Login") 

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))
  
@app.route("/user/<username>")
def profile(username):
  return f"{escape(username)}\'s Profile"

@app.errorhandler(404)
def page_not_found(error):
  return render_template('page_not_found.html', title = '404'), 404

if __name__ == "__main__":
  app.run(debug=True)