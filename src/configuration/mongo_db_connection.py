import os
import sys
import pymongo
import certifi

from src.logger import logging # custom logging module
from src.exception import CustomException
from src.constants import DATABASE_NAME, MONGODB_URL_KEY

# Load the certificate authority file to avoid timeout errors when connecting to MongoDB
ca = certifi.where()

class MongoDBClient():
    """
    A MongoDB client manager that establishes and maintains a single shared
    MongoDB connection across the entire application.

    Attributes
    ----------
    client : MongoClient
        A shared MongoClient instance reused by all MongoDBClient objects.
    database : Database
        The specific database instance selected for this client.
    database_name : str
        Name of the database the client is connected to.
    """
    client = None

    def __init__(self, databaseName: str = DATABASE_NAME):
        """
        Initialize the MongoDBClient by creating or reusing a shared MongoDB connection.

        Parameters
        ----------
        database_name : str, optional
            The name of the MongoDB database to connect to. The default value comes
            from the global `DATABASE_NAME` constant.

        Raises
        ------
        customException
            If the MongoDB URL environment variable is missing or if a connection
            error occurs during initialization.
        """
        try:
            if MongoDBClient.client is None:
                mongo_db_url = os.getenv(MONGODB_URL_KEY)
                if mongo_db_url is None:
                    raise Exception(f"Environment variable '{MONGODB_URL_KEY}' is not set.")
                
            MongoDBClient.client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)

            self.client = MongoDBClient.client
            self.database = self.client[databaseName]
            self.databaseName = databaseName
            logging.info("MongoDB connection is successful.")

        except Exception as e:
            raise CustomException(e, sys) from e