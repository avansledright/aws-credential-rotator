#!/usr/bin/env python3

import boto3
import base64
import logging
import os
import sys
import urllib3
from botocore.exceptions import ClientError
from kubernetes import client, config

# Disable SSL warnings for CRC self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get required environment variables
    username = os.environ.get('TARGET_USERNAME')
    secret_name = os.environ.get('SECRET_NAME', 'aws-credentials')
    namespace = os.environ.get('NAMESPACE', 'default')
    
    if not username:
        logger.error("TARGET_USERNAME environment variable is required")
        sys.exit(1)
    
    try:
        # Initialize AWS IAM client
        iam = boto3.client('iam')
        logger.info(f"Starting key rotation for user: {username}")
        
        # Get current keys
        current_keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']
        active_keys = [k for k in current_keys if k['Status'] == 'Active']
        inactive_keys = [k for k in current_keys if k['Status'] == 'Inactive']
        logger.info(f"Found {len(active_keys)} active keys, {len(inactive_keys)} inactive keys")
        
        # If at 2-key limit and there's an inactive key, delete it
        if len(current_keys) >= 2 and inactive_keys:
            for inactive_key in inactive_keys:
                logger.info(f"Deleting inactive key: {inactive_key['AccessKeyId']}")
                iam.delete_access_key(UserName=username, AccessKeyId=inactive_key['AccessKeyId'])
            logger.info("Cleanup complete")

        # Create new access key
        logger.info("Creating new access key")
        new_key = iam.create_access_key(UserName=username)['AccessKey']
        logger.info(f"Created new key: {new_key['AccessKeyId']}")
        
        # Update OpenShift secret
        logger.info(f"Updating OpenShift secret '{secret_name}' in namespace '{namespace}'")
        
        # Load Kubernetes config
        try:
            config.load_incluster_config()
            logger.info("Using in-cluster configuration")
        except:
            # Check for explicit token-based auth (for containers)
            k8s_host = os.environ.get('KUBERNETES_SERVICE_HOST')
            k8s_port = os.environ.get('KUBERNETES_SERVICE_PORT')
            k8s_token = os.environ.get('KUBERNETES_TOKEN')
            
            if k8s_host and k8s_port and k8s_token:
                logger.info(f"Using token-based auth to {k8s_host}:{k8s_port}")
                configuration = client.Configuration()
                configuration.host = f"https://{k8s_host}:{k8s_port}"
                configuration.api_key = {"authorization": f"Bearer {k8s_token}"}
                configuration.verify_ssl = False  # For CRC self-signed certs
                client.Configuration.set_default(configuration)
            else:
                try:
                    config.load_kube_config()
                    logger.info("Using kubeconfig file")
                except Exception as e:
                    logger.error(f"Failed to load Kubernetes config: {e}")
                    logger.error("Make sure you're logged into OpenShift with 'oc login' or set KUBERNETES_* env vars")
                    raise
        
        v1 = client.CoreV1Api()
        
        # Prepare secret data (base64 encoded)
        secret_data = {
            'AWS_ACCESS_KEY_ID': base64.b64encode(new_key['AccessKeyId'].encode()).decode(),
            'AWS_SECRET_ACCESS_KEY': base64.b64encode(new_key['SecretAccessKey'].encode()).decode()
        }
        
        # Update or create secret
        try:
            # Try to patch existing secret
            v1.patch_namespaced_secret(
                name=secret_name,
                namespace=namespace,
                body=client.V1Secret(data=secret_data)
            )
            logger.info("Updated existing secret")
        except client.ApiException as e:
            if e.status == 404:
                # Create new secret
                v1.create_namespaced_secret(
                    namespace=namespace,
                    body=client.V1Secret(
                        metadata=client.V1ObjectMeta(name=secret_name),
                        data=secret_data
                    )
                )
                logger.info("Created new secret")
            else:
                raise
        
        # Deactivate old keys
        for key in active_keys:
            logger.info(f"Deactivating old key: {key['AccessKeyId']}")
            iam.update_access_key(
                UserName=username,
                AccessKeyId=key['AccessKeyId'],
                Status='Inactive'
            )
        
        logger.info("Key rotation completed successfully")
        
    except ClientError as e:
        logger.error(f"AWS error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()