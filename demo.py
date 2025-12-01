from src.pipeline.training_pipeline import TrainPipeline

import os
import sys
import pymongo
import certifi

from src.logger import logging # custom logging module
from src.exception import CustomException
from src.constants import DATABASE_NAME, MONGODB_URL_KEY
from src.configuration.mongo_db_connection import MongoDBClient

# Load the certificate authority file to avoid timeout errors when connecting to MongoDB
ca = certifi.where()

if __name__ == "__main__":
    pipeline = TrainPipeline()
    pipeline.run_pipeline()
#     # mongo_db_url = os.getenv(MONGODB_URL_KEY)
#     # print(mongo_db_url)
# # mongodb+srv://ashishsoni295work_db_user:4dGUedp95sdSB3oI@vehicle-insurance-clust.frymii4.mongodb.net/?appName=Vehicle-Insurance-Cluster
#     uri = "mongodb+srv://ashishsoni295work_db_user:4dGUedp95sdSB3oI@vehicle-insurance-clust.frymii4.mongodb.net/?appName=Vehicle-Insurance-Cluster"
#     # MongoDBClient.client = pymongo.MongoClient(uri, tlsCAFile=ca)
# set MONGODB_URL=mongodb+srv://ashishsoni295work_db_user:4dGUedp95sdSB3oI@vehicle-insurance-clust.frymii4.mongodb.net/?appName=Vehicle-Insurance-Cluster