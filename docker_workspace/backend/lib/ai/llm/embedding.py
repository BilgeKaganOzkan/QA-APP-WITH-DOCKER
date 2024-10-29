from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import os
import sys

class Embedding:
    """
    @brief Manages the embedding model for generating vector representations.

    This class initializes an embedding model using the OpenAI API and
    provides a method to retrieve the embedding instance.

    Attributes:
    - embedding (OpenAIEmbeddings): The embedding model instance.
    """
    
    def __init__(self, model_name: str) -> None:
        """
        @brief Initializes the Embedding instance with the specified model.

        This method loads environment variables from a .env file and
        creates an instance of the OpenAI embeddings model.

        @param model_name (str): The name of the model to be used for embeddings.
        """
        load_dotenv()  # Load environment variables from .env file

        try:
            # Initialize the OpenAIEmbeddings with the specified model name and API key
            self.embedding = OpenAIEmbeddings(model=model_name, openai_api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            # Print the error and exit if initialization fails
            print(e)
            sys.exit(-1)
    
    def get_embedding(self) -> OpenAIEmbeddings:
        """
        @brief Retrieves the embedding model instance.

        @return The OpenAIEmbeddings instance used for generating embeddings.
        """
        return self.embedding  # Return the initialized embedding instance