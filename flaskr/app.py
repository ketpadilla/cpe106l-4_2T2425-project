from flask import Flask
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

@app.before_request
def check_db_connection():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

from .routes import configure_routes
configure_routes(app, WEB_NAME='Trackabite')

if __name__ == "__main__":
    app.run(debug=True)