FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

ARG USER_UID=1000
ARG USER_GID=1000

RUN groupmod -g ${USER_GID} vscode \
 && usermod -u ${USER_UID} -g ${USER_GID} vscode \
 && chown -R vscode:vscode /home/vscode

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Default working directory
WORKDIR /workspace

RUN sudo chown -R vscode:vscode /workspace