import os
import sys
from pandas import DataFrame
from sklearn.model_selection import train_test_split

from src.logger import logging
from src.exception import CustomException
from src.data_access.data_source import DataFromMongo

from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact

class DataIngestion:
    """
    Handles the extraction of raw data from the feature store (MongoDB),
    stores it locally, and performs the train-test split for downstream
    machine learning components.

    This class is the first step of the ML pipeline and produces
    DataIngestionArtifact objects containing file paths for the processed
    training and testing datasets.
    """

    def __init__(self, data_ingestion_config: DataIngestionConfig = DataIngestionConfig()):
        """
        Initialize the DataIngestion component with the provided configuration.

        Parameters
        ----------
        data_ingestion_config : DataIngestionConfig, optional
            Configuration object containing parameters such as MongoDB collection name,
            feature store path, train/test split ratio, and output file paths.
        """
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise CustomException(e, sys) from e

    def export_data_into_feature_store(self) -> DataFrame:
        """
        Extract raw data from MongoDB and save it into the local feature store.

        This method:
        - Connects to MongoDB using `DataFromMongo`
        - Retrieves the specified collection as a pandas DataFrame
        - Logs dataset shape
        - Creates the feature store directory if not present
        - Saves the DataFrame as a CSV file in the feature store location

        Returns
        -------
        DataFrame
            The DataFrame fetched from MongoDB.
        """
        try:
            logging.info("Started exporting data from MongoDB")
            mongo_data = DataFromMongo()
            df_mongo_data = mongo_data.download_collection_as_dataframe(collectionName= self.data_ingestion_config.collection_name)
            logging.info(f"data retrievd with shape: {df_mongo_data.shape}")
            
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok = True)

            logging.info(f"saving retrieved data into feature store file path: {feature_store_file_path} as csv...")
            df_mongo_data.to_csv(feature_store_file_path, index= False, header= True)
            logging.info("data saved.")
            return df_mongo_data
        
        except Exception as e:
            raise CustomException(e, sys) from e

    def split_train_test_data(self, dataframe: DataFrame) -> None:
        """
        Split the dataset into training and testing subsets and store them as CSV files.

        The split ratio is taken from `data_ingestion_config.train_test_split_ratio`.
        The resulting train and test CSVs are saved to the paths specified in the
        configuration object.

        Parameters
        ----------
        dataframe : DataFrame
            The dataset to split into train and test subsets.
        """
        logging.info("Splitting the dataframe into train and test")
        try:
            train_data, test_data = train_test_split(dataframe, test_size= self.data_ingestion_config.train_test_split_ratio, random_state= 42)
            
            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok= True)

            logging.info("dataframe splitted, saving...")
            train_data.to_csv(self.data_ingestion_config.training_file_path, index= False, header= True)
            test_data.to_csv(self.data_ingestion_config.testing_file_path, index= False, header= True)

            logging.info("train and test data saved.")
        except Exception as e:
            raise CustomException(e, sys) from e

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        """
        Execute the complete data ingestion workflow.

        This method:
        - Fetches data from MongoDB and stores it in the local feature store
        - Splits the data into training and testing sets
        - Saves the resulting datasets to disk
        - Produces a DataIngestionArtifact containing all relevant metadata

        Returns
        -------
        DataIngestionArtifact
            Object containing file paths for training and testing datasets.
        """
        logging.info("Starting data ingestion...")
        try:
            dataFrame = self.export_data_into_feature_store()
            self.split_train_test_data(dataframe= dataFrame)

            data_ingestion_artifact = DataIngestionArtifact(trained_file_path= self.data_ingestion_config.training_file_path, test_file_path= self.data_ingestion_config.testing_file_path)
            logging.info(f"data ingestion completed. Data Ingestion Artifact: {data_ingestion_artifact}")

            return data_ingestion_artifact
        except Exception as e:
            raise CustomException(e, sys) from e