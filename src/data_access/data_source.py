import sys
import pandas as pd
import numpy as np
from typing import Optional

from src.configuration.mongo_db_connection import MongoDBClient
from src.exception import CustomException
from src.logger import logging

class DataFromMongo():
    """
    Utility class for retrieving data from MongoDB and converting collections
    into pandas DataFrames.

    This class internally uses MongoDBClient to establish and reuse a MongoDB
    connection. It provides a simple interface for loading entire collections
    as DataFrames with basic cleaning applied.
    """

    def __init__(self):
        """
        Initialize the DataFromMongo helper class by creating a MongoDBClient instance.

        The MongoDBClient handles connection management and ensures a shared MongoDB
        client is reused across the application. This constructor simply attaches
        that client to the current instance.
        """
        try:
            self.mongoClient = MongoDBClient()
        except Exception as e:
            raise CustomException(e, sys)
        
    def download_collection_as_dataframe(self, collectionName: str, databaseName: Optional[str] = None) -> pd.DataFrame:
        """
        Load a MongoDB collection as a pandas DataFrame.

        This method retrieves the specified collection from either the default
        database or a custom database (if provided), converts the collection
        documents into a DataFrame, performs basic preprocessing, and returns the
        result.

        Pre-Processing steps:
        -----------------
        - Drop the 'id' column if present (MongoDB-specific cleanup)
        - Replace "na" string values with NaN for compatibility with pandas

        Parameters
        ----------
        collectionName : str
            Name of the MongoDB collection to fetch.
        databaseName : Optional[str], default=None
            Optional database name. If not provided, the default database used by
            MongoDBClient is selected.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing all documents from the collection.
        """
        try:
            if databaseName is None:
                collection = self.mongoClient.database[collectionName]
            else:
                collection = self.mongoClient[databaseName][collectionName]
            
            logging.info("fetching data from MongoDB...")
            df = pd.DataFrame(list(collection.find()))
            logging.info(f"Data fetched with len: {len(df)}")
            if "id" in df.columns.to_list():
                df = df.drop(columns=["id"], axis=1)
            df.replace({"na":np.nan}, inplace= True)
            return df
        except Exception as e:
            raise CustomException(e, sys)
