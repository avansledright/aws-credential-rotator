# AWS Key Rotator with OpenShift Integration

A simple Python script that rotates AWS IAM access keys and automatically updates OpenShift secrets with the new credentials.

## What it does

1. **Creates new AWS access keys** for the specified IAM user
2. **Updates OpenShift secret** with the new credentials
3. **Deactivates old keys** (marks them as inactive for safety)

## Prerequisites

- Docker
- OpenShift CLI (`oc`) installed and logged in
- AWS credentials configured in `~/.aws/credentials`
- IAM user with appropriate permissions

## Files

- `scripts/rotate_keys.py` - Main Python script
- `scripts/requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `run_local.sh` - Bash script to build and run the container

## Setup

1. Make sure you're logged into OpenShift:
   ```bash
   oc login -u developer -p developer https://api.crc.testing:6443
   oc project your-namespace
   ```

2. Make the runner script executable:
   ```bash
   chmod +x run_local.sh
   ```

## Usage

```bash
./run_local.sh <IAM_USERNAME> [SECRET_NAME] [NAMESPACE]
```

### Examples

```bash
# Basic usage (secret: aws-credentials, namespace: default)
./run_local.sh my-iam-user

# Custom secret name
./run_local.sh my-iam-user my-aws-secret

# Custom secret name and namespace
./run_local.sh my-iam-user aws-credentials my-namespace
```

## Environment Variables

- `TARGET_USERNAME` - AWS IAM username (required)
- `SECRET_NAME` - OpenShift secret name (default: `aws-credentials`)
- `NAMESPACE` - OpenShift namespace (default: `default`)

## OpenShift Secret Format

The script creates/updates a secret with these keys:
- `AWS_ACCESS_KEY_ID` - The new access key ID
- `AWS_SECRET_ACCESS_KEY` - The new secret access key

## Notes

- Old keys are deactivated but not deleted for safety
- If the user has 2 keys (AWS limit), inactive keys are automatically deleted first
- The script works with CodeReady Containers (CRC) and regular OpenShift clusters
- SSL verification is disabled for CRC self-signed certificates

## Dependencies

```
boto3
kubernetes
```