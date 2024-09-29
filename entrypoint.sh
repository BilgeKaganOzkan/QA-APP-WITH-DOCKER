#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define paths
CONTAINER_WORKSPACE="/home/gktrkQA/docker_workspace"
START_SCRIPT="start_app.sh"

# Navigate to the project directory
cd "$CONTAINER_WORKSPACE"

# Check for specific files that should exist in the repository
REQUIRED_FILES=("$START_SCRIPT")  # Add any required files here

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: Required file $file not found in the $CONTAINER_WORKSPACE."
        exit 1
    fi
done

# Ensure the start script is executable
if [ ! -x "$START_SCRIPT" ]; then
    echo "Making $START_SCRIPT executable..."
    chmod +x "$START_SCRIPT"
fi

# Start the application
echo "Starting the application with $START_SCRIPT..."
./"$START_SCRIPT"