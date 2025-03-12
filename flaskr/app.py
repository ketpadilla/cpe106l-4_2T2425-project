"""Trackabite Flask Application.

This module initializes a Flask application, connects to a MongoDB database,
and configures routes for the Trackabite web application.
"""

from flask import Flask
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from .utils import debug_border
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

uri = os.getenv("MONGO_URI")
database = os.getenv("DATABASE")
food_api = os.getenv("FOOD_API")

client = MongoClient(uri, server_api=ServerApi('1'))
db = client[database]

@app.before_request
def connect_to_db():
    """Connect to the MongoDB database and log connection details.

    This function is executed before every request to ensure the application
    is connected to the MongoDB database. It pings the database to confirm
    the connection and logs statistics about the database, including storage
    size, data size, total documents, and index size.

    Raises:
        Exception: If the connection to the database fails, an error message
            is printed to the console.
    """
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")

        stats = db.command("dbStats")
        collections = db.list_collection_names()

        print()
        debug_border()
        print("Collections in the database:", collections)
        print(f"Database Storage Size: {stats['storageSize']} bytes")
        print(f"Database Data Size: {stats['dataSize']} bytes")
        print(f"Total Documents: {stats['objects']}")
        print(f"Index Size: {stats['indexSize']} bytes")
        debug_border()

    except Exception as e:
        print(f"Error: {e}")

from .routes import configure_routes
configure_routes(app, WEB_NAME='Trackabite')

if __name__ == "__main__":
    """Run the Flask application in debug mode.

    This block ensures the Flask application runs in debug mode when the script
    is executed directly. Debug mode provides detailed error messages and
    automatic reloading during development.
    """
    app.run(debug=True)
# %%
