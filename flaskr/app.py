from flask import Flask
from markupsafe import escape
from .routes import configure_routes

app = Flask(__name__)
configure_routes(app, WEB_NAME = 'Trackabite')

if __name__ == "__main__":
  app.run(debug=True)