#!/bin/bash

# Usage: ./run_key_rotator.sh <USERNAME> [SECRET_NAME] [NAMESPACE]

USERNAME="$1"
SECRET_NAME="${2:-aws-credentials}"
NAMESPACE="${3:-default}"

if [ -z "$USERNAME" ]; then
    echo "Usage: $0 <USERNAME> [SECRET_NAME] [NAMESPACE]"
    exit 1
fi

docker build -t aws-key-rotator .

docker run --rm \
    --network host \
    -v ~/.aws:/root/.aws:ro \
    -v ~/.kube:/root/.kube:ro \
    -e TARGET_USERNAME="$USERNAME" \
    -e SECRET_NAME="$SECRET_NAME" \
    -e NAMESPACE="$NAMESPACE" \
    aws-key-rotator