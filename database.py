# database.py

from pymongo import MongoClient

# Initialize the MongoDB client and specify the database
client = MongoClient("mongodb://localhost:27017/")
db = client['rider_driver_pooling']  # Replace with your database name
route_triples_collection = db['route_triples']  # Collection name for storing route triples
