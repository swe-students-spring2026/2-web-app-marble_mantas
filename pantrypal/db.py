import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DBNAME = os.getenv("MONGO_DBNAME", "pantrypal")

client = MongoClient(MONGO_URI)
db = client[MONGO_DBNAME]

# Collections
items = db["items"]
