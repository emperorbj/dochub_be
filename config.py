from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "dochubDB"
USER_COLLECTION = "users"
FILE_COLLECTION="converted_file"

client = None

async def init_db():
    global client
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        await client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

async def close_db():
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")

def get_user_collection():
    return client[DB_NAME][USER_COLLECTION]


def get_file_collection():
    return client[DB_NAME][FILE_COLLECTION]


