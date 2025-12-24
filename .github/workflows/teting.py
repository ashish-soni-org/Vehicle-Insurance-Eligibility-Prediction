import os
import json
import boto3
from botocore.exceptions import ClientError

# Configuration from Environment Variables
REGION = os.getenv("AWS_REGION")
SECRET_NAME = os.getenv("SECRET_FILE_NAME")

def get_client():
    return boto3.client("secretsmanager", region_name=REGION)

response = get_client().get_secret_value(
    SecretId=SECRET_NAME
)

secret_string = response
secrets = json.loads(secret_string)

def main():

    output_file = os.getenv('GITHUB_OUTPUT')
    
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"runner_details={secret_string}\n")
            f.write(f"available_services_details={secrets}\n")
            # f.write(f"runner_details={json.dumps(secret_string)}\n")
            # f.write(f"available_services_details={json.dumps(secrets)}\n")

if __name__ == "__main__":
    main()