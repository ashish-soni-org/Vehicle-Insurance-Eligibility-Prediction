import os
import boto3

from src.constants import REGION_NAME

class S3Client:
    """
    Wrapper class for creating and managing a singleton AWS S3 client and resource.

    This class initializes:
        - boto3 S3 *client* (used for low-level operations like upload/download)
        - boto3 S3 *resource* (used for high-level, object-oriented S3 operations)

    AUTHENTICATION:
    It relies on the standard boto3 credential chain. When running on an EC2 instance
    with an assigned IAM Role, boto3 will automatically detect and use the instance 
    profile credentials. No environment variables or hardcoded keys are required.

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
            - RELIES ON IAM ROLE: Does not require explicit access keys.
        """
        if S3Client.s3_resource is None or S3Client.s3_client is None:
            
            # Initialize without passing explicit credentials.
            # Boto3 will automatically find the IAM Role credentials from the EC2 metadata.
            S3Client.s3_resource = boto3.resource(
                's3',
                region_name=region_name
            )
            
            S3Client.s3_client = boto3.client(
                's3',
                region_name=region_name
            )
            
        self.s3_resource = S3Client.s3_resource
        self.s3_client = S3Client.s3_client