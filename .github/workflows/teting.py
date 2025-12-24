import os
import json
import boto3
import sys
from botocore.exceptions import ClientError

# Configuration from Environment Variables
REGION = os.getenv("AWS_REGION")
SECRET_NAME = os.getenv("SECRET_FILE_NAME")

def get_client():
    """Initializes the Boto3 Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=REGION)

def main():
    client = get_client()

    try:
        # Fetch the secret from AWS
        response = client.get_secret_value(SecretId=SECRET_NAME)
        
        # The actual secret is a string in the 'SecretString' key
        secret_content = response.get('SecretString')
        
        if not secret_content:
            print("Error: SecretString is empty.")
            sys.exit(1)

        # Parse and re-dump to ensure it's a clean JSON string for the output
        secrets_dict = json.loads(secret_content)
        
        # Prepare GITHUB_OUTPUT
        output_file = os.getenv('GITHUB_OUTPUT')
        
        if output_file:
            with open(output_file, "a") as f:
                # We pass the JSON string so it can be parsed by 'jq' in later jobs
                f.write(f"runner_details={secrets_dict["runner"]}\n")
                f.write(f"available_services_details={json.dumps(secrets_dict)}\n")
        
        print(f"Successfully fetched and exported secret: {SECRET_NAME}")

    except ClientError as e:
        print(f"AWS Error: {e.response['Error']['Message']}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Validate environment variables
    if not REGION or not SECRET_NAME:
        print("Missing AWS_REGION or SECRET_FILE_NAME environment variables.")
        sys.exit(1)
    main()