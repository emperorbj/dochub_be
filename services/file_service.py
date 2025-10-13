from datetime import datetime, timezone
from bson import ObjectId
from config import get_file_collection

async def save_file_record(
    user_id: str,
    original_filename: str,
    converted_filename: str,
    file_type: str,
    conversion_type: str,
    cloud_url: str,
    status: str = "completed",
    file_size: int = 0
):
    """
    Save a record of a converted file to the database
    """
    collection = get_file_collection()
    record = {
        "user_id": ObjectId(user_id),
        "original_filename": original_filename,
        "converted_filename": converted_filename,
        "file_type": file_type,
        "conversion_type": conversion_type,
        "file_size": file_size,
        "cloud_url": cloud_url,
        "status": status,
        "created_at": datetime.now(timezone.utc)
    }

    result = await collection.insert_one(record)
    saved_record = await collection.find_one({"_id": result.inserted_id})

    # Convert ObjectId to str for response
    saved_record["_id"] = str(saved_record["_id"])
    saved_record["user_id"] = str(saved_record["user_id"])
    return saved_record


async def get_user_files(user_id: str):
    """
    List all converted files for a specific user
    """
    collection = get_file_collection()
    cursor = collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)

    files = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        files.append(doc)
    return files


async def get_file_by_id(file_id: str):
    """
    Get a specific converted file by its ID
    """
    collection = get_file_collection()
    doc = await collection.find_one({"_id": ObjectId(file_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
    return doc


async def delete_file(file_id: str, user_id: str):
    """
    Delete a file record owned by the user
    """
    collection = get_file_collection()
    result = await collection.delete_one({
        "_id": ObjectId(file_id),
        "user_id": ObjectId(user_id)
    })
    return result.deleted_count > 0
