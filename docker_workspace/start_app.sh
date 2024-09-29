#!/bin/bash

DIRECTORY=$(pwd)
BACKEND_PATH="$DIRECTORY/backend"
FRONTEND_PATH="$DIRECTORY/frontend"

VENV_BACKEND_PATH="$BACKEND_PATH/.venv"
LOG_BACKEND_PATH="$BACKEND_PATH/.log"
TEMP_DB_BACKEND_PATH="$BACKEND_PATH/.temp_databases"
ENV_BACKEND_PATH="$BACKEND_PATH/.env"
NODE_MODULES_FRONTEND_PATH="$FRONTEND_PATH/node_modules"

PYTHON_VERSION=3.11.9
NPM_VERSION=18.19.1

SESSION_NAME="LangChainSQLApp"
BACKEND_WINDOW="backend"
FRONTEND_WINDOW="frontend"
 #redis-cli CONFIG SET notify-keyspace-events Ex"
SET_ENV_BACKEND="cd $BACKEND_PATH; source $VENV_BACKEND_PATH/bin/activate;"
SET_ENV_FRONTEND="cd $FRONTEND_PATH; nvm use $NPM_VERSION;"


ensure_node_version() {
    if [ -f "$FRONTEND_PATH/.nvmrc" ]; then
        echo "Ensuring correct Node.js version from .nvmrc..."
        nvm install
        nvm use
    else
        echo ".nvmrc not found. Using default Node.js version."
    fi
}

install_frontend_dependencies() {
    echo "Installing frontend dependencies..."
    cd "$FRONTEND_PATH"
    npm install
}

install_backend_dependencies() {
    echo "Creating virtual environment in $VENV_BACKEND_PATH..."
    python -m venv $VENV_BACKEND_PATH

    source $VENV_BACKEND_PATH/bin/activate
    pip install -r "$BACKEND_PATH/requirements.txt"
    deactivate
}

if [ ! -d "$LOG_BACKEND_PATH" ]; then
    echo "Creating $LOG_BACKEND_PATH directory..."
    mkdir -p "$LOG_BACKEND_PATH"
fi

if [ ! -d "$TEMP_DB_BACKEND_PATH" ]; then
    echo "Creating $TEMP_DB_BACKEND_PATH directory..."
    mkdir -p "$TEMP_DB_BACKEND_PATH"
fi

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

echo "Pyenv root: $PYENV_ROOT"
echo "Python version set by pyenv: $(pyenv version)"
echo "Python executable: $(which python)"
echo "Python version: $(python --version)"

pyenv local $PYTHON_VERSION

if [ ! -d "$VENV_BACKEND_PATH" ]; then
    install_backend_dependencies
else
    echo ".venv already exists. Skipping virtual environment setup."
fi
echo "$ENV_BACKEND_PATH"
if [ -e "$ENV_BACKEND_PATH" ]; then
    echo ".env file already exists. Skipping to create env file."
else
    echo "Creating .env ile on $ENV_BACKEND_PATH..."
    touch "$ENV_BACKEND_PATH"
    echo -e "\n\n!!!!Please write your openai api key: "
    read openai_api_key
    echo -e "\n\n"
    echo "OPENAI_API_KEY=$openai_api_key" >> $ENV_BACKEND_PATH
fi

ensure_node_version

if [ -d "$NODE_MODULES_FRONTEND_PATH" ]; then
    echo "Dependencies are installed."
else
    echo "Dependencies are not installed."
    install_frontend_dependencies
fi

cd "$FRONTEND_PATH"
echo "Building frontend application..."
npm run build

cd "$DIRECTORY"

#redis-server &

tmux new-session -d -s $SESSION_NAME -n $BACKEND_WINDOW
tmux send-keys -t $SESSION_NAME:$BACKEND_WINDOW "$SET_ENV_BACKEND"
tmux send-keys -t $SESSION_NAME:$BACKEND_WINDOW "; while true; do python -B app.py; done"

sleep 3

tmux new-window -t $SESSION_NAME -n $FRONTEND_WINDOW
tmux send-keys -t $SESSION_NAME:$FRONTEND_WINDOW "$SET_ENV_FRONTEND"
tmux send-keys -t $SESSION_NAME:$FRONTEND_WINDOW "; while true; do npm start; done"

sleep 5

exec bash