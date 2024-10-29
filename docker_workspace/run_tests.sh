#!/bin/bash

# Check if enough arguments are provided
if [ "$#" -lt 2 ]; then
  echo "Usage: ./run_test.sh <project_part> <test_type> [test_name]"
  exit 1
fi

# Assign arguments to variables
PROJECT_PART=$(echo "$1" | xargs)
TEST_TYPE=$(echo "$2" | xargs)
TEST_NAME=$(echo "$3" | xargs)

# Debugging output to verify variable contents
echo "PROJECT_PART: '$PROJECT_PART'"
echo "TEST_TYPE: '$TEST_TYPE'"
echo "TEST_NAME: '$TEST_NAME'"

# Set base path and test command based on project part
if [ "$PROJECT_PART" == "backend" ]; then
  cd backend
  BASE_PATH="tests"
  TEST_COMMAND="pytest"
elif [ "$PROJECT_PART" == "frontend" ]; then
  cd frontend
  BASE_PATH="src/__tests__"
  TEST_COMMAND="npm test"
else
  echo "Error: Invalid project part. Use 'backend' or 'frontend'."
  exit 1
fi

# Set test path based on test type
if [ "$TEST_TYPE" == "unit" ]; then
  TEST_PATH="$BASE_PATH/unit"
elif [ "$TEST_TYPE" == "integration" ] || [ "$TEST_TYPE" == "e2e" ]; then
  # Check if user_database_name is set to test_user_db in backend config for backend integration or e2e tests
  if [ "$PROJECT_PART" == "backend" ]; then
    source ./.venv/bin/activate
    CONFIG_FILE="config/config.yaml"
        USER_DB_NAME=$(python3 -c "
import yaml 
with open('$CONFIG_FILE') as f: 
  config = yaml.safe_load(f) 
  print(config['server'].get('user_database_name', ''))")
    if [ "$USER_DB_NAME" != "test_user_db" ]; then
      echo "Error: 'user_database_name' in $CONFIG_FILE must be set to 'test_user_db' for $TEST_TYPE tests."
      exit 1
    fi
  fi

  if [ "$TEST_TYPE" == "integration" ]; then
    TEST_PATH="$BASE_PATH/integration"
  elif [ "$TEST_TYPE" == "e2e" ]; then
    if [ "$PROJECT_PART" == "frontend" ]; then
      # Use Cypress for frontend e2e tests
      echo "Running frontend e2e tests with Cypress..."
      XDG_RUNTIME_DIR=/tmp xvfb-run -a npx cypress run --headless --spec "src/__tests__/e2e_test/e2eTest.cy.js" --config baseUrl=http://localhost:3000,supportFile=false
      exit 0
    else
      TEST_PATH="$BASE_PATH/e2e_test"
    fi
  fi
elif [ "$TEST_TYPE" == "all" ]; then
  TEST_PATH=$BASE_PATH
  TEST_TYPE=all
else
  echo "Error: Invalid test type. Use 'unit', 'integration', or 'e2e'."
  exit 1
fi

# Check if the test directory exists
if [ ! -d "$TEST_PATH" ]; then
  echo "Error: Test path '$TEST_PATH' does not exist."
  exit 1
fi

# Run the specified test(s)
if [[ "$PROJECT_PART" == "backend" && "$TEST_NAME" == "all" ]]; then
  # Run all tests in the backend test directory if test_name is "all"
  echo "Running all backend tests in $TEST_PATH..."
  for test_file in $(find "$TEST_PATH" -name "test_*.py"); do
    echo "Running: $test_file"
    pytest "$test_file"
    
    # Check the result of each test file
    if [ $? -ne 0 ]; then
      echo "$test_file failed."
      exit 1
    fi
  done
  echo "$TEST_NAME $PROJECT_PART tests completed successfully."
else
  # Run a specific test file or directory if TEST_NAME is provided
  if [ -n "$TEST_NAME" ]; then
    TEST_DIR="$TEST_PATH/$TEST_NAME"
    if [ -d "$TEST_DIR" ]; then
      echo "Running all tests in directory $TEST_DIR..."
      $TEST_COMMAND "$TEST_DIR"
    elif [ -f "$TEST_DIR" ]; then
      echo "Running test file $TEST_DIR..."
      $TEST_COMMAND "$TEST_DIR"
    else
      echo "Error: Test path or file '$TEST_DIR' does not exist."
      exit 1
    fi
  else
    # Run all tests in the specified directory if no specific test name is provided
    echo "Running all tests in $TEST_PATH..."
    $TEST_COMMAND "$TEST_PATH"
  fi
fi