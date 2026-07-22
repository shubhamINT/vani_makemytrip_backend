#!/bin/bash
set -euo pipefail  # exit on error, unset var, or failed pipe

# Check if env is present
if [ ! -f ".env" ]; then
    echo "Error: .env file is not present"
    exit 1
fi

# Update the code from git (repo default branch is master, not main)
echo "Pulling latest code..."
git pull origin master

# Build and run; --wait blocks until the healthcheck passes
echo "Building and starting services..."
docker compose up -d --build --wait

# Cleanup dangling images/build cache (does not touch volumes)
echo "Cleaning up..."
docker image prune -f

echo "Deployment completed successfully."
