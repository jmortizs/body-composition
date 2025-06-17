import os

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()

CONNECTION_STRING = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# validate env variables
if not CONNECTION_STRING:
    raise ValueError("MONGO_URI is not set")
if not DATABASE_NAME:
    raise ValueError("DATABASE_NAME is not set")

class MongoDBClient:
    _client: AsyncMongoClient = None

    @classmethod
    async def get_client(cls):
        if cls._client is None:
            try:
                cls._client = AsyncMongoClient(CONNECTION_STRING)
            except Exception as e:
                raise ValueError(f"Failed to connect to MongoDB: {e}")
        return cls._client

    @classmethod
    async def close_client(cls):
        if cls._client:
            await cls._client.close()
            cls._client = None

    @classmethod
    async def get_database(cls):
        client = await cls.get_client()
        return client[DATABASE_NAME]
