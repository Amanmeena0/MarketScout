from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from config.settings import mongodb_uri

client = MongoClient(mongodb_uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    db = client['market_analysis']
except Exception as e:
    print(e)
    