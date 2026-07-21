# pyrefly: ignore [missing-import]
from pymongo import MongoClient

db = None
users_collection = None

def init_db(app):
    global db, users_collection
    mongodb_uri = app.config.get('MONGODB_URI')
    if mongodb_uri:
        try:
            mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            db = mongo_client['home-file-server']
            users_collection = db['users']
            # Create unique index on username
            users_collection.create_index('username', unique=True)
            print("✓ Connected to MongoDB successfully")
        except Exception as e:
            print(f"✗ MongoDB connection error: {e}")
            db = None
            users_collection = None
