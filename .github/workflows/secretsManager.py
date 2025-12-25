import os
import json
import boto3
import sys
from botocore.exceptions import ClientError

# Configuration from Environment Variables
REGION = os.getenv("AWS_REGION")
ACTION = os.getenv("ACTION_TYPE")
SECRET_NAME = os.getenv("SECRET_FILE_NAME")
TARGET_REPO = os.getenv("REPO_NAME") 
SERVICES_ENV = os.getenv("SERVICES", "")

# Constants
CREATE_FILE_STRUCTURE = "CREATE_FILE_STRUCTURE"
SERVICE_REQUEST = "SERVICE_REQUEST"

def get_client():
    """Initializes the Boto3 Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=REGION)

def handle_secret():
    client = get_client()
    initial_payload = {"repos": {}}

    try:
        if ACTION == CREATE_FILE_STRUCTURE:
            try:
                client.create_secret(
                    Name=SECRET_NAME,
                    SecretString=json.dumps(initial_payload),
                    Description="Contains all secrets related to EC2 instance Production Server"
                )
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceExistsException':
                    client.put_secret_value(
                        SecretId=SECRET_NAME,
                        SecretString=json.dumps(initial_payload)
                    )
                else:
                    raise e

        elif ACTION == SERVICE_REQUEST:
            response = client.get_secret_value(SecretId=SECRET_NAME)
            current_secrets = json.loads(response['SecretString'])
            
            requested_list = [s.strip() for s in SERVICES_ENV.split(";") if s.strip()]
            
            repo_services = current_secrets.get("repos", {}).get(TARGET_REPO, {}).get("services", {})
            
            result_map = {}
            needs_provisioning = False
            
            for service in requested_list:
                val = repo_services.get(service, "")
                result_map[service] = val
                # If any requested service is missing its value, flag for provisioning
                if not val:
                    needs_provisioning = True
            
            # Export to GitHub Output
            output_file = os.getenv('GITHUB_OUTPUT')
            if output_file:
                with open(output_file, "a") as f:
                    f.write(f"required_services={json.dumps(result_map)}\n")
                    f.write(f"needs_provisioning={'true' if needs_provisioning else 'false'}\n")
            
            print(f"Processed {TARGET_REPO}. Provisioning Required: {needs_provisioning}")

    except Exception as e:
        print(f"Error managing secret: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    if not all([REGION, SECRET_NAME, ACTION]):
        print("Missing required environment variables")
        sys.exit(1)
        
    handle_secret()