FROM ubuntu:24.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractiv

# Set timezone and install dependencies
RUN ln -fs /usr/share/zoneinfo/Turkey /etc/localtime \
    && apt update && apt install -y tzdata \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* \
    && dpkg-reconfigure --frontend noninteractive tzdata

# Install basic utilities and tools
RUN apt update \
    && apt install software-properties-common -y \
    && apt install -y apt-utils \
    && apt install -y \
        bash-completion \
        build-essential \
        make \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libpq-dev \
        llvm \
        libncurses5-dev \
        libncursesw5-dev \
        xz-utils \
        tk-dev \
        libffi-dev \
        liblzma-dev \
        ca-certificates \
        curl \
        gedit \
        git \
        gnome-terminal \
        language-pack-en \
        less \
        locales \
        locate \
        nano \
        openssh-server \
        pkg-config \
        sudo \
        tmux \
        vim \
        wget \
        python3 \
        python3-pip \
        nodejs \
        postgresql-client \
        xsel \
        doxygen \
        xvfb \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

RUN id -u ubuntu &>/dev/null && userdel -r ubuntu || echo "User 'ubuntu' does not exist."

# Add a user and set password
RUN useradd -ms /bin/bash -g root -G sudo gktrkQA \
    && echo 'gktrkQA:qaapp' | chpasswd

# Install and configure Redis
#RUN apt update \
#    && apt install -y redis-server \
#    && sed -i 's/^# notify-keyspace-events ""/notify-keyspace-events Ex/' /etc/redis/redis.conf \
#    && apt clean \
#    && rm -rf /var/lib/apt/lists/*

# Copy entrypoint files
COPY entrypoint.sh /home/gktrkQA/entrypoint.sh
RUN chmod +x /home/gktrkQA/entrypoint.sh

# Switch to non-root user
USER gktrkQA

# Set up environment variables
ENV HOME="/home/gktrkQA"
ENV PYENV_ROOT="$HOME/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"
ENV PYTHON_VERSION="3.11.9"
ENV NPM_VERSION="18.19.1"

# Install pyenv
RUN curl -o- https://pyenv.run | bash \
    && echo 'export PYENV_ROOT="$HOME/.pyenv"' >> $HOME/.bashrc \
    && echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> $HOME/.bashrc \
    && echo 'eval "$(pyenv init --path)"' >> $HOME/.bashrc \
    && echo 'eval "$(pyenv init -)"' >> $HOME/.bashrc \
    && echo 'eval "$(pyenv virtualenv-init -)"' >> $HOME/.bashrc \
    && pyenv install "$PYTHON_VERSION"

# Set up environment variables
ENV NVM_DIR="$HOME/.nvm"
ENV PATH="$NVM_DIR/versions/node/v$NPM_VERSION/bin:$PATH"

# Install nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash \
    && echo -e '\n# NVM setup' >> $HOME/.bashrc \
    && echo 'export NVM_DIR="$HOME/.nvm"' >> $HOME/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm' >> $HOME/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion' >> $HOME/.bashrc

# Install the desired Node.js version using nvm
RUN bash -lc "source $NVM_DIR/nvm.sh && nvm install $NPM_VERSION"

# Switch to root user and copy entrypoint.sh
USER root
ENTRYPOINT ["/home/gktrkQA/entrypoint.sh"]

# Create docker_workspace
RUN mkdir -p /home/gktrkQA/docker_workspace && \
    chown -R gktrkQA:root /home/gktrkQA/docker_workspace && \
    chmod -R 755 /home/gktrkQA/docker_workspace

# Switch to non-root user
USER gktrkQA

# Set working directory
WORKDIR /home/gktrkQA/docker_workspace