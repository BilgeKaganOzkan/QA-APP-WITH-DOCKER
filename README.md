 # SQL & RAG-Powered QA Chatbot
 
 This containerized application provides a powerful question-answering (QA) chatbot that leverages SQL and retrieval-augmented generation (RAG) capabilities. Users can upload CSV or PDF files, which are then converted into temporary databases that can be queried dynamically. These temporary databases are automatically removed upon refreshing the webpage, exiting the application, or after a preset timeout. Backend configurations can be customized in the `config` file located within the `backend` directory.
 
 ## Key Features
 
 - **Current Capabilities**: 
   - The **SQL Query Panel** enables users to upload CSV files that are processed into a temporary SQL database for querying.
   - The **RAG Panel** allows users to upload PDF files, converting them into structured data that the chatbot can answer questions about, limiting responses strictly to the content in the uploaded documents. Unlike standard LLMs, the chatbot does not generate speculative answers.
 
 - **Enhanced Querying and Analysis**:
   - In the **SQL Panel**, users can uncover connections between uploaded datasets by asking questions and exploring relationships, even performing simple statistical analyses.
 
 - **Conversation History**:
   - Each session maintains a conversation history, helping improve response relevance and accuracy with each subsequent query.
 
 ## Getting Started
 
 To start the application, simply execute the `run.sh` script, which sets up the environment and launches the container:
 
 ```bash
 ./run.sh
 ```
 
 During setup, you’ll be prompted to enter your OpenAI access token. Ensure you input the correct token, as it is essential for the program’s functionality.
 
 Once the container is running, access the application at `http://172.20.0.22:3000/`.
 
 Alternatively, the project has been deployed at [https://www.qaapp.com](https://www.qaapp.com) for ease of use without setup. However, note that the application is currently under development and may contain some bugs.
 
 ## Using the Project
 
 To use the project, please follow these steps:
 
 1. **Account Registration**: You must have an account to access the project. If you don’t have an account, please create one via the signup screen.
 
 2. **Login and Initial Screen**: Once logged in, you’ll be welcomed by the main screen with the **SQL Bot** interface.
 
 3. **Using SQL Agent**:
    - To start a conversation with the SQL Agent, first upload a CSV file by clicking on the paperclip icon in the **Query Input** field.
    - Once uploaded, you can start interacting with the bot by entering queries related to your data. During the conversation, you can upload additional files, provided you stay within the maximum file limit.
 
 4. **Switching to RAG Agent**:
    - If you prefer to chat with the **RAG Agent** (for PDF-based queries), switch to the RAG Panel by clicking the arrow icon in the upper left corner.
    - Similar to the SQL Agent, you can start by uploading a PDF document in the RAG Panel and then proceed with your questions.
 
 5. **Data and History Management**:
    - Each time you switch panels, all previous history and uploaded files are cleared.
    - Additionally, if you refresh the page, your session will end automatically. This means no user data is stored on the server, ensuring your data remains private.
 
 ## Documentation
 
 Both the backend and frontend code are written to support Doxygen format, enabling easy access to comprehensive documentation. You can find the documentation for each codebase in the following directories:
 
 - **Backend Documentation**: `backend/docs`
 - **Frontend Documentation**: `frontend/docs`
 
 To begin using the documentation, open the `index.html` file located within these directories. This file serves as the entry point for accessing detailed descriptions and usage instructions for the code.
 
 ## Testing
 
 The project is designed with full testability in mind. You can run all tests from the project’s `docker_workspace` directory using the `./run_test <project_part> <test_type> <test_name>` command. This script accepts the following parameters:
 
 - `project_part`: Specify `backend` to test the backend code or `frontend` to test the frontend code.
 - `test_type`: Choose the type of tests to run: `unit`, `integration`, or `e2e`.
 - `test_name`: Specify `all` to run all tests in the specified directory, or provide the name of a specific test file or subdirectory you want to execute.
 
 ### Examples
 
 1. Run all backend tests:
    ```bash
    ./run_test.sh backend all
    ```
 
 2. Run a specific backend unit test file (e.g., `test_sample.py`):
    ```bash
    ./run_test.sh backend unit test_sample
    ```
 
 3. Run e2e tests:
    ```bash
    ./run_test.sh frontend e2e
    ```
 
 ### Important Note
 For backend integration tests and end-to-end (E2E) tests to work correctly:

 1. Set the `user_database_name` in `backend/config/config.yaml` to `test_user_db`.
 2. Ensure that the `User` table in `test_user_db` is empty before running tests.
 
 ## Technologies Used
 
 The project uses Docker Compose for containerization. The backend incorporates the following technologies:
 
 - **PostgreSQL** for SQL storage
 - **FAISS** for vector storage
 - **Redis** for session management
 
 ## Limitations
 
 Due to server capacity constraints on the [https://www.qaapp.com](https://www.qaapp.com) deployment, the following limitations apply:
 
 - Each session allows a maximum of:
   - 5 PDF files on the RAG Panel
   - 5 CSV files on the SQL Panel
 - A maximum of 10 iterations per response generation in the background.
 
 For higher accuracy and greater flexibility, download the project and adjust these limitations directly in the backend configuration.
 
 ---
 
This project stands apart from conventional LLM models like ChatGPT and Gemini AI, as responses are strictly based on the uploaded documents, avoiding fabricated answers. The SQL panel provides robust capabilities for analyzing and exploring relationships within user-uploaded datasets.
