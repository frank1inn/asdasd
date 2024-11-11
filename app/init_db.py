from pymongo import MongoClient
import os
from bson import ObjectId
def init_db():
    client = MongoClient(os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/'))
    db = client.quant_platform
    
    # Create test user if not exists
    if db.users.count_documents({'username': 'test'}) == 0:
        user_id = ObjectId()
        db.users.insert_one({
            '_id': user_id,
            'username': 'test',
            'password': 'test123',  # In production, use hashed passwords
            'strategy_ids': []
        })
        print("Test user created successfully!")
    else:
        print("Test user already exists!")

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed!")

