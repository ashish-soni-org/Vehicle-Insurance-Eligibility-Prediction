import os
import json
import boto3
import sys
from botocore.exceptions import ClientError

# Configuration from Environment Variables
REGION = os.getenv("AWS_REGION")
ACTION = os.getenv("ACTION_TYPE")
SECRET_NAME = os.getenv("SECRET_FILE_NAME")
# The repo we are currently targeting for the service lookup
TARGET_REPO = os.getenv("REPO_NAME") 

# Constants
CREATE_FILE_STRUCTURE = "CREATE_FILE_STRUCTURE"
SERVICE_REQUEST = "SERVICE_REQUEST"
SERVICES = "SERVICES"

def get_client():
    """Initializes the Boto3 Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=REGION)

def handle_secret():
    client = get_client()
    
    # Default payload for structure creation
    initial_payload = {
        "repos": {}
    }

    try:
        if ACTION == CREATE_FILE_STRUCTURE:
            try:
                client.create_secret(
                    Name=SECRET_NAME,
                    SecretString=json.dumps(initial_payload),
                    Description="This Contains all the secrets related to EC2 instance Production Server"
                )
                print(f"Successfully created new secret: {SECRET_NAME}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceExistsException':
                    client.put_secret_value(
                        SecretId=SECRET_NAME,
                        SecretString=json.dumps(initial_payload)
                    )
                    print(f"Secret {SECRET_NAME} already exists. Reset structure.")
                else:
                    raise e

        elif ACTION == SERVICE_REQUEST:
            # 1. Fetch the current secret data
            response = client.get_secret_value(SecretId=SECRET_NAME)
            current_secrets = json.loads(response['SecretString'])
            
            # 2. Parse the requested services (e.g., "S3;ECR")
            services_env = os.getenv(SERVICES, "")
            requested_list = [s.strip() for s in services_env.split(";") if s.strip()]
            
            # 3. Navigate to the specific repo's services
            # Path: repos -> TARGET_REPO -> services
            repo_services = current_secrets.get("repos", {}).get(TARGET_REPO, {}).get("services", {})
            
            # 4. Build the output dictionary
            # If service exists, map to value; else map to ""
            result_map = {}
            for service in requested_list:
                result_map[service] = repo_services.get(service, "")
            
            # 5. Export to GitHub Output for use in CI/CD logs/jobs
            output_file = os.getenv('GITHUB_OUTPUT')
            if output_file:
                with open(output_file, "a") as f:
                    f.write(f"required_services={json.dumps(result_map)}\n")
            
            print(f"Service Request processed for {TARGET_REPO}: {result_map}")

    except Exception as e:
        print(f"Error managing secret: {str(e)}")
        sys.exit(1)

def upsert_repo(secret_dict, repo_name, services: dict):
    """Utility to modify the dictionary structure locally"""
    repos = secret_dict.setdefault("repos", {})
    repo = repos.setdefault(repo_name, {"services": {}})
    repo["services"].update(services)
    return secret_dict

if __name__ == '__main__':
    if not all([REGION, SECRET_NAME, ACTION]):
        print("Missing required environment variables (AWS_REGION, SECRET_FILE_NAME, ACTION_TYPE)")
        sys.exit(1)
        
    handle_secret()