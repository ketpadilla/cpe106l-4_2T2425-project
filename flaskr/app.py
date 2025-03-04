from flask import Flask, session, redirect, url_for, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
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
  try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")

    stats = db.command("dbStats")
    collections = db.list_collection_names()

    print()
    print ("-" * 25)
    print("Collections in the database:", collections)
    print(f"Database Storage Size: {stats['storageSize']} bytes")
    print(f"Database Data Size: {stats['dataSize']} bytes")
    print(f"Total Documents: {stats['objects']}")
    print(f"Index Size: {stats['indexSize']} bytes")
    print ("-" * 25, end="\n\n")

  except Exception as e:
    print(f"Error: {e}")

from .routes import configure_routes
configure_routes(app, WEB_NAME='Trackabite')

if __name__ == "__main__":
    app.run(debug=True)