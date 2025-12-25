import os
import json
import boto3
import sys
from botocore.exceptions import ClientError

# ------------------------------------------------------------------
# Configuration from Environment Variables
# ------------------------------------------------------------------
REGION = os.getenv("AWS_REGION")
ACTION = os.getenv("ACTION_TYPE")
SECRET_NAME = os.getenv("SECRET_FILE_NAME")
TARGET_REPO = os.getenv("REPO_NAME") 

# JSON string from Terraform Output: 
# { "s3_buckets": { "repo-name": "bucket-id" }, "ecr_repositories": { "repo-name": "ecr-name" } }
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
        # ------------------------------------------------------------------
        # 1. Fetch Existing Secret
        # ------------------------------------------------------------------
        full_data = {"repos": {}}
        try:
            response = client.get_secret_value(SecretId=SECRET_NAME)
            if 'SecretString' in response:
                full_data = json.loads(response['SecretString'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Secret {SECRET_NAME} not found. A new one will be created.")
            else:
                raise e

        # ------------------------------------------------------------------
        # 2. Action Handler: CREATE_FILE_STRUCTURE
        # ------------------------------------------------------------------
        if ACTION == CREATE_FILE_STRUCTURE:
            # Initialize structure. If a runner host is passed, store it.
            runner_host = os.getenv("SELF_HOSTED_RUNNER")
            
            if "repos" not in full_data:
                full_data["repos"] = {}
                
            if runner_host:
                full_data["runner_host"] = runner_host

            client.put_secret_value(SecretId=SECRET_NAME, SecretString=json.dumps(full_data))
            print(f"SUCCESS: Infrastructure secrets initialized for {SECRET_NAME}")

        # ------------------------------------------------------------------
        # 3. Action Handler: SERVICE_REQUEST (Check Availability)
        # ------------------------------------------------------------------
        elif ACTION == SERVICE_REQUEST:
            requested_env = os.getenv("SERVICES", "")
            # Split "ECR;S3" into ["ECR", "S3"]
            requested_list = [s.strip() for s in requested_env.split(";") if s.strip()]
            
            repo_services = full_data.get("repos", {}).get(TARGET_REPO, {}).get("services", {})
            
            result_map = {}
            needs_provisioning = False

            for req in requested_list:
                val = repo_services.get(req, "")
                result_map[req] = val
                if not val:
                    needs_provisioning = True
            
            # Write outputs for GitHub Actions
            output_file = os.getenv('GITHUB_OUTPUT')
            if output_file:
                with open(output_file, "a") as f:
                    f.write(f"required_services={json.dumps(result_map)}\n")
                    f.write(f"needs_provisioning={'true' if needs_provisioning else 'false'}\n")
            
            print(f"Check Complete. Needs Provisioning: {needs_provisioning}")

        # ------------------------------------------------------------------
        # 4. Action Handler: ADD_SERVICES (Update after Provisioning)
        # ------------------------------------------------------------------
        elif ACTION == ADD_SERVICES:
            try:
                tf_data = json.loads(SERVICES_JSON)
            except json.JSONDecodeError:
                print(f"ERROR: Invalid JSON data received: {SERVICES_JSON}")
                sys.exit(1)
            
            # Normalize target key (Terraform keys are lowercase)
            target_key = TARGET_REPO.lower() if TARGET_REPO else ""
            updates = {}

            # Map Terraform Output Keys -> Secret Manager Keys
            # 1. Map S3
            if "s3_buckets" in tf_data and target_key in tf_data["s3_buckets"]:
                updates["S3"] = tf_data["s3_buckets"][target_key]
            
            # 2. Map ECR
            if "ecr_repositories" in tf_data and target_key in tf_data["ecr_repositories"]:
                updates["ECR"] = tf_data["ecr_repositories"][target_key]

            if not updates:
                print(f"WARNING: No resources found for repo '{TARGET_REPO}' in provisioned map.")
            
            # Update the nested structure
            repos = full_data.setdefault("repos", {})
            repo_node = repos.setdefault(TARGET_REPO, {})
            services_node = repo_node.setdefault("services", {})
            
            services_node.update(updates)
            
            client.put_secret_value(
                SecretId=SECRET_NAME,
                SecretString=json.dumps(full_data)
            )
            print(f"SUCCESS: Updated {TARGET_REPO} in Secrets Manager with: {updates}")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    if not all([REGION, SECRET_NAME, ACTION]):
        print("CRITICAL: Missing required environment variables (REGION, SECRET_FILE_NAME, ACTION_TYPE).")
        sys.exit(1)
    handle_secret()