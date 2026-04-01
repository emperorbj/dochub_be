from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
# Supabase Storage bucket (must exist in your Supabase project; override with SUPABASE_BUCKET).
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "docsbucket")
DB_NAME = "dochubDB"
USER_COLLECTION = "users"
FILE_COLLECTION = "converted_file"
JOBS_COLLECTION = "conversion_jobs"

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


def get_jobs_collection():
    return client[DB_NAME][JOBS_COLLECTION]

