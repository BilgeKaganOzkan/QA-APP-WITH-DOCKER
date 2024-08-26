# SQL-Powered QA Chatbot

This application is a containerized solution that converts uploaded CSV files into temporary databases in the background, enabling users to interact with a SQL-powered Question Answering (QA) chatbot. These temporary databases are automatically deleted when the user refreshes the webpage, exits the application, or after a certain timeout period. The backend configuration can be customized through the `config` file located in the `backend` directory.

## Overview

- **Current Capabilities**: Users can upload CSV files, which are converted into temporary databases for querying.
- **Upcoming Features**: A version with Retrieval-Augmented Generation (RAG) capabilities will be introduced in the next phase.

## How to Run

To start the application, simply run the `run.sh` script. This will set up the environment and start the container.

```
./run.sh
```

After the program start and container terminal is available, you can access the program from `http://172.18.0.22:3000/` address.
