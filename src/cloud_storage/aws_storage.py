import os
import sys
import pickle
import pandas as pd
from io import StringIO
from typing import Union, List
from botocore.exceptions import ClientError
from mypy_boto3_s3.service_resource import Bucket


from src.logger import logging
from src.exception import CustomException
from src.configuration.aws_connection import S3Client

class SimpleStorageService:
    """
    High-level utility class for interacting with AWS S3.

    This class provides helper methods for:
        - Uploading and downloading files
        - Reading CSVs and model objects directly from S3
        - Checking if S3 keys exist
        - Creating folders inside S3 buckets
        - Loading machine learning models stored in S3
        - Converting S3 objects into pandas DataFrames

    It uses the shared, singleton S3 client/resource created by `S3Client`.
    """

    def __init__(self):
        """
        Initialize an instance of SimpleStorageService.

        Creates S3 resource and client by instantiating the shared S3Client.
        Ensures credentials are loaded once and reused across the application.
        """
        s3_client = S3Client()
        self.s3_resource = s3_client.s3_resource
        self.s3_client = s3_client.s3_client

    def get_bucket(self, bucket_name: str) -> Bucket:
        """
        Get the S3 bucket resource.

        Args:
            bucket_name (str): Name of the S3 bucket.

        Returns:
            Bucket: boto3 S3 Bucket object.
        """
        try:
            bucket = self.s3_resource.Bucket(bucket_name)
            return bucket
        except Exception as e:
            raise CustomException(e, sys) from e

    def s3_key_path_available(self, bucket_name: str, s3_key: str) -> bool:
        """
        Check if a given S3 key (file or folder) exists inside a bucket.

        Args:
            bucket_name (str): Name of the S3 bucket.
            s3_key (str): Full S3 key or prefix to check.

        Returns:
            bool: True if at least one object exists with the provided prefix.
        """
        try:
            bucket = self.get_bucket(bucket_name)
            file_objects = [file_objects for file_objects in bucket.objects.filter(Prefix = s3_key)]
            return len(file_objects) > 0
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_file_object(self, bucket_name: str, file_name: str) -> Union[List, object]: # Union[X, Y] means the value can be either type X or type Y
        """
        Retrieve one or multiple S3 file objects matching a prefix.

        Args:
            bucket_name (str): S3 bucket name.
            file_name (str): S3 key prefix (file or folder).

        Returns:
            Union[list, object]:
                - Single object if exactly one match
                - List of objects if multiple matches
        """
        try:
            bucket = self.get_bucket(bucket_name)
            file_objects = [file_objects for file_objects in bucket.objects.filter(file_name)]
            func = lambda x: x[0] if len(x) == 1 else x
            file_objs = func(file_objects)
            return file_objs
        except Exception as e:
            raise CustomException(e, sys) from e

    def load_model(self, model_name: str, bucket_name: str, model_dir: str = None) -> object:
        """
        Load and unpickle a ML model stored in an S3 bucket.

        Args:
            model_name (str): File name of the model inside S3.
            bucket_name (str): Bucket name.
            model_dir (str, optional): Optional directory inside S3.

        Returns:
            object: Deserialized Python model object.
        """
        try:
            model_file = model_dir + "/" + model_name if model_dir else model_name
            file_objects = self.get_file_object(bucket_name, model_file)
            model_obj = self.read_object(file_objects, decode = False)
            model = pickle.loads(model_obj)
            logging.info("production model loaded from s3 bucket")
        
            return model
        except Exception as e:
            raise CustomException(e, sys) from e
        
    def create_folder(self, folder_name: str, bucket_name: str) -> None:
        """
        Create a "folder" inside an S3 bucket (prefix ending with '/').

        Args:
            folder_name (str): Name of the S3 folder.
            bucket_name (str): S3 bucket name.

        Notes:
            S3 does not have real folders — they are just key prefixes.
        """
        try:
            self.s3_resource.Object(bucket_name, folder_name).load()
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                folder_obj = folder_name + "/"
                self.s3_resource.put_object(Bucket= bucket_name, Key= folder_obj)

    def upload_file(self, from_filename: str, to_filename: str, bucket_name: str, remove: bool = True) -> None:
        """
        Upload a local file to an S3 bucket.

        Args:
            from_filename (str): Local file path.
            to_filename (str): S3 key to upload to.
            bucket_name (str): S3 bucket name.
            remove (bool): If True, delete local file after upload.
        """
        try:
            logging.info(f"uploading {from_filename} to {to_filename} in {bucket_name}")
            self.s3_resource.meta.client.upload_file(from_filename, bucket_name, to_filename)
            logging.info(f"uploaded {from_filename} to {to_filename} in {bucket_name}")

            # delete the local file if 'remove' is True
            if remove:
                os.remove(from_filename)
                logging.info(f"removed local file {from_filename} after uploading")
        except Exception as e:
            raise CustomException(e, sys) from e

    def upload_df_as_csv(self, dataframe: pd.DataFrame, local_filename: str, bucket_filename: str, bucket_name: str) -> None:
        """
        Save a pandas DataFrame as CSV and upload it to S3.

        Args:
            dataframe (DataFrame): DataFrame to upload.
            local_filename (str): Temporary local CSV filename.
            bucket_filename (str): S3 key for upload.
            bucket_name (str): S3 bucket name.
        """
        try:
            # save dataframe locally then upload it
            dataframe.to_csv(local_filename, index= None, header= True)
            self.upload_file(local_filename, bucket_filename, bucket_name)
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_df_from_object(self, object_: object) -> pd.DataFrame:
        """
        Convert an S3 object into a pandas DataFrame.

        Args:
            object_ (object): boto3 object representing a CSV file in S3.

        Returns:
            DataFrame: Loaded DataFrame.
        """
        try:
            content = self.read_object(object_, make_readable= True)
            dataframe = pd.read_csv(content, na_values= "na")
            return dataframe
        except Exception as e:
            raise CustomException(e, sys) from e

    def read_csv(self, file_name: str, bucket_name: str) -> pd.DataFrame:
        """
        Read a CSV directly from S3 into a pandas DataFrame.

        Args:
            file_name (str): S3 key of the CSV file.
            bucket_name (str): Name of the bucket.

        Returns:
            DataFrame: Loaded data.
        """
        try:
            csv_obj = self.get_file_object(bucket_name, file_name)
            dataframe = self.get_df_from_object(csv_obj)
            return dataframe
        except Exception as e:
            raise CustomException(e, sys) from e

    @staticmethod
    def read_object(self, object_name: str, decode: bool = True, make_readable: bool = False) -> Union[StringIO, str, bytes]:
        """
        Read raw or decoded content from an S3 object.

        Args:
            object_name: boto3 S3 object reference.
            decode (bool): Whether to decode bytes to UTF-8 text.
            make_readable (bool): If True, wrap text content in a StringIO buffer.

        Returns:
            Union[StringIO, str, bytes]:
                - StringIO: if make_readable=True
                - str: if decode=True
                - bytes: if decode=False
        """
        try:
            # read and decode the object content if 'decode= True'
            func = (
                lambda: object_name.get()["Body"].read().decode()
                if decode else object_name.get()["Body"].read()
            )

            # convert StringIO if 'make_readable= True'
            conv_func = lambda: StringIO(func()) if make_readable else func()

            return conv_func()
        except Exception as e:
            raise CustomException(e, sys) from e
