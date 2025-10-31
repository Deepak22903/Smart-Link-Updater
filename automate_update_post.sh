#!/bin/bash

# Define the post ID to update
POST_ID=105

# Define the base URL for the API
BASE_URL="http://localhost:8000"

# Trigger the update-post endpoint
RESPONSE=$(curl -s -X POST "$BASE_URL/update-post/$POST_ID")

# Extract the task ID and status URL from the response
TASK_ID=$(echo $RESPONSE | jq -r '.task_id')
STATUS_URL=$(echo $RESPONSE | jq -r '.status_url')

# Print the initial response
echo "Response from update-post: $RESPONSE"

# Poll the task status until completion
while true; do
  echo "Polling task status at: $BASE_URL$STATUS_URL"
  STATUS_RESPONSE=$(curl -s "$BASE_URL$STATUS_URL")
  echo "Task status response: $STATUS_RESPONSE"

  # Check if the task is completed
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  if [ "$STATUS" == "completed" ]; then
    echo "Task completed."
    break
  fi

  # Wait for 5 seconds before polling again
  echo "Task not completed. Retrying in 5 seconds..."
  sleep 5
done
