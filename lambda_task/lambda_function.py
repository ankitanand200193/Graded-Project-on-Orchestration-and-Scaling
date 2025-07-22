import os
import json
import boto3
from datetime import datetime
from pymongo import MongoClient

s3 = boto3.client('s3')

def lambda_handler(event, context):
    mongo_uri = os.environ['MONGO_URI']  # MongoDB connection URI
    bucket = os.environ['S3_BUCKET']     # S3 bucket name
    prefix = os.environ.get('S3_PREFIX', 'mongodb-backups/')  # S3 folder prefix

    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client.get_default_database()

    # Generate a timestamped filename
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"/tmp/mongo_backup_{timestamp}.json"

    # Create backup data
    backup_data = {}
    for collection_name in db.list_collection_names():
        backup_data[collection_name] = list(db[collection_name].find())

    # Write backup to /tmp (Lambda temp storage)
    with open(filename, "w") as f:
        json.dump(backup_data, f, default=str)

    # Upload to S3
    s3_key = f"{prefix}mongo_backup_{timestamp}.json"
    s3.upload_file(filename, bucket, s3_key)

    return {
        "status": "success",
        "s3_key": s3_key
    }
