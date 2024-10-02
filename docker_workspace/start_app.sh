#!/bin/bash

DIRECTORY=$(pwd)
BACKEND_PATH="$DIRECTORY/backend"
FRONTEND_PATH="$DIRECTORY/frontend"

VENV_BACKEND_PATH="$BACKEND_PATH/.venv"
LOG_BACKEND_PATH="$BACKEND_PATH/.log"
NODE_MODULES_FRONTEND_PATH="$FRONTEND_PATH/node_modules"

PYTHON_VERSION=3.11.9
NPM_VERSION=18.19.1

SESSION_NAME="LangChainSQLApp"
BACKEND_WINDOW="backend"
FRONTEND_WINDOW="frontend"

SET_ENV_BACKEND="cd $BACKEND_PATH && python -m venv ./.venv && pip install -r requirements.txt && source $VENV_BACKEND_PATH/bin/activate;"
SET_ENV_FRONTEND="cd $FRONTEND_PATH && nvm use $NPM_VERSION && npm install;"


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

tmux new-session -d -s $SESSION_NAME -n $BACKEND_WINDOW
tmux send-keys -t $SESSION_NAME:$BACKEND_WINDOW "$SET_ENV_BACKEND"
tmux send-keys -t $SESSION_NAME:$BACKEND_WINDOW "&& while true; do python -B app.py; done"
tmux send-keys -t $SESSION_NAME:$BACKEND_WINDOW ENTER

sleep 150

tmux new-window -t $SESSION_NAME -n $FRONTEND_WINDOW
tmux send-keys -t $SESSION_NAME:$FRONTEND_WINDOW "$SET_ENV_FRONTEND"
tmux send-keys -t $SESSION_NAME:$FRONTEND_WINDOW "&& npm run build && while true; do npm install -g serve && serve -s build; done"
tmux send-keys -t $SESSION_NAME:$FRONTEND_WINDOW ENTER

sleep 5

exec bash