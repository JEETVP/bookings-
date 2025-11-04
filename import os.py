import os
from dotenv import load_dotenv
from date import datetime
from pymongo import MongoClient, ASCENDING
from bson import ObjectId

load_dotenv()

MONGODB_URI= os.getenv ("MONGODB_URI", "mongodb://localhost27017")
DB_NAME = os.getenv("DB.name")