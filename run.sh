#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define the Docker Compose service name for your app
SERVICE_NAME="qa_app"

# Define the Docker workspace path on the host
HOST_WORKSPACE="$(pwd)/docker_workspace"

# Check if the docker_workspace directory exists on the host, if not, create it
if [ ! -d "$HOST_WORKSPACE" ]; then
    echo "$HOST_WORKSPACE directory is empty!!!"
    exit 1
fi

# Check if Docker Compose is installed
if ! [ -x "$(command -v docker compose)" ]; then
  echo 'Error: docker compose is not installed.' >&2
  exit 1
fi

# Build the Docker images using docker-compose (it will only build if necessary)
echo "Building the Docker images using docker compose..."
docker compose build

# Start the services using docker-compose
echo "Starting the services using docker-compose..."
docker compose up -d

# Check if the services are running
if [[ "$(docker compose ps -q $SERVICE_NAME)" == "" ]]; then
    echo "Error: $SERVICE_NAME service is not running."
    exit 1
else
    echo "$SERVICE_NAME service is running."
fi