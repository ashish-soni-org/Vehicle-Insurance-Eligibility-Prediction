import os
import json

def main():
    # Data to pass to other jobs
    runner_info = {
        "status": "active",
        "region": "us-east-1",
        "env": "production"
    }
    
    # 1. Standard Output for visibility
    print(f"Generating metadata for runner...")

    # 2. Writing to GITHUB_OUTPUT
    # GitHub provides the path to a file via the GITHUB_OUTPUT environment variable
    output_file = os.getenv('GITHUB_OUTPUT')
    
    if output_file:
        with open(output_file, "a") as f:
            # Simple string output
            f.write("hello_msg=Hello World from Python!\n")
            # Complex JSON output (useful for matrices or detailed objects)
            f.write(f"runner_details={json.dumps(runner_info)}\n")
            f.write("trigger_deploy=true\n")
            
    print("Metadata successfully written to GITHUB_OUTPUT.")

if __name__ == "__main__":
    main()