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

# This should be a JSON string like: {"S3": "my-bucket-name", "ECR": "my-repo-name"}
SERVICES_JSON = os.getenv("PROVISIONED_MAP", "{}")

# Constants
CREATE_FILE_STRUCTURE = "CREATE_FILE_STRUCTURE"
SERVICE_REQUEST = "SERVICE_REQUEST"
ADD_SERVICES = "ADD_SERVICES"

def get_client():
    """Initializes the Boto3 Secrets Manager client."""
    return boto3.client("secretsmanager", region_name=REGION)

def handle_secret():
    client = get_client()
    
    try:
        # Fetch current secret content for any operational action
        try:
            response = client.get_secret_value(SecretId=SECRET_NAME)
            full_data = json.loads(response['SecretString'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException' and ACTION == CREATE_FILE_STRUCTURE:
                full_data = {"repos": {}}
            else:
                raise e

        if ACTION == CREATE_FILE_STRUCTURE:
            full_data = {"repos": {}}
            client.put_secret_value(SecretId=SECRET_NAME, SecretString=json.dumps(full_data))
            print(f"Structure reset/created: {SECRET_NAME}")

        elif ACTION == SERVICE_REQUEST:
            # Logic for checking service availability (as implemented previously)
            requested_env = os.getenv("SERVICES", "")
            requested_list = [s.strip() for s in requested_env.split(";") if s.strip()]
            repo_services = full_data.get("repos", {}).get(TARGET_REPO, {}).get("services", {})
            
            result_map = {service: repo_services.get(service, "") for service in requested_list}
            needs_provisioning = any(val == "" for val in result_map.values())
            
            output_file = os.getenv('GITHUB_OUTPUT')
            if output_file:
                with open(output_file, "a") as f:
                    f.write(f"required_services={json.dumps(result_map)}\n")
                    f.write(f"needs_provisioning={'true' if needs_provisioning else 'false'}\n")

        elif ACTION == ADD_SERVICES:
            # 1. Parse the provisioned data from Terraform
            try:
                new_provisioned_data = json.loads(SERVICES_JSON)
            except json.JSONDecodeError:
                print(f"ERROR: Invalid JSON data received: {SERVICES_JSON}")
                sys.exit(1)
            
            # 2. Update the nested structure: repos -> {repo} -> services -> {Type: Name}
            repos = full_data.setdefault("repos", {})
            repo_node = repos.setdefault(TARGET_REPO, {})
            services_node = repo_node.setdefault("services", {})
            
            # 3. Update with actual service names
            # Expected new_provisioned_data: {"S3": "ashish-repo1-bucket", "ECR": "ashish-repo1-ecr"}
            services_node.update(new_provisioned_data)
            
            # 4. Save back to Secrets Manager
            client.put_secret_value(
                SecretId=SECRET_NAME,
                SecretString=json.dumps(full_data)
            )
            print(f"SUCCESS: Updated {TARGET_REPO} in Secrets Manager with: {new_provisioned_data}")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    if not all([REGION, SECRET_NAME, ACTION]):
        print("CRITICAL: Missing required environment variables.")
        sys.exit(1)
    handle_secret()