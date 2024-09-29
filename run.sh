#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define the Docker image name
IMAGE_NAME="qa-app"

# Define the Docker workspace path on the host and container
HOST_WORKSPACE="$(pwd)/docker_workspace"
CONTAINER_WORKSPACE="/home/gktrkQA/docker_workspace"

# Check if the docker_workspace directory exists on the host, if not, create it
if [ ! -d "$HOST_WORKSPACE" ]; then
    echo "$HOST_WORKSPACE directory is empty!!!"
    exit 1
fi

# Build the Docker image if it doesn't exist
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
    echo "Docker image $IMAGE_NAME does not exist. Building the image..."
    docker build -t $IMAGE_NAME .
else
    echo "Docker image $IMAGE_NAME already exists."
fi

# Check if the Docker network exists, if not, create it
if ! docker network ls | grep -q "qa-app-network"; then
    echo "Docker network qa-app-network does not exist. Creating the network..."
    docker network create --subnet=172.18.0.0/16 qa-app-network
else
    echo "Docker network qa-app-network already exists."
fi

# Run the Docker container and mount the docker_workspace directory
echo "Running Docker container from image $IMAGE_NAME..."
docker run -it --rm \
    -v "$HOST_WORKSPACE:$CONTAINER_WORKSPACE" \
    --network qa-app-network --ip 172.18.0.22 \
    --privileged \
    --name="${IMAGE_NAME}" \
    $IMAGE_NAME