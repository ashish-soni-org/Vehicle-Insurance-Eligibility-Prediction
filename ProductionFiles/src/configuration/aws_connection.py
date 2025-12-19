import os
import boto3

from src.constants import REGION_NAME, AWS_ACCESS_KEY_ID_ENV_KEY, AWS_SECRET_ACCESS_KEY_ENV_KEY

class S3Client:
    """
    Wrapper class for creating and managing a singleton AWS S3 client and resource.

    This class initializes:
        - boto3 S3 *client* (used for low-level operations like upload/download)
        - boto3 S3 *resource* (used for high-level, object-oriented S3 operations)

    It reads AWS credentials from environment variables and ensures that S3
    connections are created only once during the application's lifecycle,
    improving performance and avoiding redundant boto3 initializations.

    Environment Variables Required:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY

    Attributes:
        s3_client (boto3.client): Shared low-level S3 client instance.
        s3_resource (boto3.resource): Shared high-level S3 resource instance.
    """
    s3_client = None
    s3_resource = None

    def __init__(self, region_name: str = REGION_NAME):
        """
        Initialize the AWS S3 client and resource if not already created.

        Args:
            region_name (str, optional):
                AWS region to connect to. Defaults to REGION_NAME constant.

        Notes:
            - Implements a *singleton pattern* at the class level.
            - Ensures only one S3 client and S3 resource are created for the entire application.
            - Credentials are pulled from environment variables for security and flexibility.
        """
        if S3Client.s3_resource == None or S3Client.s3_client == None:
            __access_key_id = os.getenv(AWS_ACCESS_KEY_ID_ENV_KEY)
            __secret_access_key = os.getenv(AWS_SECRET_ACCESS_KEY_ENV_KEY)

            if __access_key_id == None:
                raise Exception(f"Environment variable {AWS_ACCESS_KEY_ID_ENV_KEY} is not set.")
            
            if __secret_access_key == None:
                raise Exception(f"Environment variable {AWS_SECRET_ACCESS_KEY_ENV_KEY} is not set.")
            
            S3Client.s3_resource = boto3.resource('s3',
                                            aws_access_key_id=__access_key_id,
                                            aws_secret_access_key=__secret_access_key,
                                            region_name=region_name
                                            )
            S3Client.s3_client = boto3.client('s3',
                                        aws_access_key_id=__access_key_id,
                                        aws_secret_access_key=__secret_access_key,
                                        region_name=region_name
                                        )
        self.s3_resource = S3Client.s3_resource
        self.s3_client = S3Client.s3_client