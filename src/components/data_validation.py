import os
import sys
import json
import pandas as pd

from src.logger import logging
from src.exception import CustomException
from src.constants import SCHEMA_FILE_PATH
from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from src.entity.config_entity import DataValidationConfig
from src.utils.main_utils import read_yaml_file

class DataValidation:
    """
    Performs validation on ingested data before it is passed to 
    the transformation and model training stages.

    This includes:
    - Validating number of columns
    - Checking presence of required numerical & categorical columns
    - Storing validation results as a JSON report
    """

    def __init__(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_config: DataValidationConfig):
        """
        Initializes the DataValidation component.

        Args:
            data_ingestion_artifact (DataIngestionArtifact):
                Contains file paths for the train and test CSVs.
            data_validation_config (DataValidationConfig):
                Contains output file paths and configuration settings.
        """
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config = read_yaml_file(file_path = SCHEMA_FILE_PATH)
        except Exception as e:
            raise CustomException(e, sys) from e

    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        """
        Validates that the number of columns in the dataframe matches the schema.

        Args:
            dataframe (DataFrame): The dataframe to validate.

        Returns:
            bool: True if column count matches schema, otherwise False.
        """
        try:
            status = len(dataframe.columns) == len(self._schema_config["columns"])
            logging.info(f"Is required columns present: {status}")
            return status
        except Exception as e:
            raise CustomException(e, sys) from e

    def is_column_exist(self, dataframe: pd.DataFrame) -> bool:
        """
        Checks if all required numerical and categorical columns exist.

        Args:
            df (DataFrame): The dataframe being validated.

        Returns:
            bool: True if all required columns exist, otherwise False.
        """
        try:
            dataframe_columns = set(dataframe.columns)

            missing_numerical = [
                col for col in self._schema_config["numerical_columns"]
                if col not in dataframe_columns
            ]

            missing_categorical = [
                col for col in self._schema_config["categorical_columns"]
                if col not in dataframe_columns
            ]

            if missing_numerical:
                logging.info(f"Missing numerical columns: {missing_numerical}")

            if missing_categorical:
                logging.info(f"Missing categorical columns: {missing_categorical}")

            return not (missing_numerical or missing_categorical)
        except Exception as e:
            raise CustomException(e, sys) from e

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        """
        Reads a CSV file and returns it as a DataFrame.

        Args:
            file_path (str): Full file path to the CSV file.

        Returns:
            DataFrame: Loaded dataframe.
        """
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise CustomException(e, sys) from e

    def initiate_data_validation(self) -> DataValidationArtifact:
        """
        Runs all validation checks:
        - Validates number of columns
        - Validates presence of required columns
        - Generates a JSON validation report
        - Returns a DataValidationArtifact for downstream pipeline stages

        Returns:
            DataValidationArtifact: The artifact containing validation status and report file path.
        """
        try:
            logging.info("Starting data validation...")
            validation_error_msg = ""
            train_df, test_df = (DataValidation.read_data(file_path= self.data_ingestion_artifact.trained_file_path), DataValidation.read_data(file_path= self.data_ingestion_artifact.test_file_path))

            # validating numbers of columns in training and test data
            status = self.validate_number_of_columns(train_df)
            if not status:
                validation_error_msg += f"columns are missing in training dataframe"
            else:
                logging.info(f"all required columns are present in training dataframe: {status}")

            status = self.validate_number_of_columns(test_df)
            if not status:
                validation_error_msg += f"columns are missing in test dataframe"
            else:
                logging.info(f"all required columns are present in testing dataframe: {status}")

            # validating column dtypes of training and test data
            status = self.is_column_exist(train_df)
            if not status:
                validation_error_msg += f"columns are missing from the training dataframe"
            else:
                logging.info(f"all categoricat/int columns are present in training dataframe: {status}")
            
            status = self.is_column_exist(test_df)
            if not status:
                validation_error_msg += f"columns are missing from the test dataframe"
            else:
                logging.info(f"all categoricat/int columns are present in test dataframe: {status}")

            # reporting the validation
            validation_status = len(validation_error_msg) == 0

            data_validation_artifact = DataValidationArtifact(
                validation_status= validation_status,
                message= validation_error_msg,
                validation_report_file_path= self.data_validation_config.validation_report_file_path
            )

            report_dir = os.path.dirname(self.data_validation_config.validation_report_file_path)
            os.makedirs(report_dir, exist_ok= True)

            validation_report = {
                "validation_status": validation_status,
                "message": validation_error_msg.strip()
            }

            with open(self.data_validation_config.validation_report_file_path, 'w') as f:
                json.dump(validation_report, f, indent= 4)

            logging.info(f"data validation artifact created and saved to JSON file, Data Validation Artifact: {data_validation_artifact}")
            return data_validation_artifact
        except Exception as e:
            raise CustomException(e, sys) from e