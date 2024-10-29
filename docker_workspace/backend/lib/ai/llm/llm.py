from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
import sys

class LLM:
    """
    @brief Manages the large language model (LLM) for generating responses.

    This class initializes a chat-based LLM using the OpenAI API and
    provides methods to invoke the model with a query and retrieve the
    model instance.

    Attributes:
    - llm (ChatOpenAI): The instance of the chat-based LLM.
    """
    
    def __init__(self, llm_model_name: str) -> None:
        """
        @brief Initializes the LLM instance with the specified model.

        This method loads environment variables from a .env file and
        creates an instance of the ChatOpenAI model.

        @param llm_model_name (str): The name of the LLM model to be used.
        """
        load_dotenv()  # Load environment variables from .env file

        try:
            # Initialize the ChatOpenAI model with specified parameters
            self.llm = ChatOpenAI(temperature=0.0, model_name=llm_model_name, openai_api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            # Print the error and exit if initialization fails
            print(e)
            sys.exit(-1)
    
    def __call__(self, query: str) -> str:
        """
        @brief Invokes the LLM with a given query.

        This method allows the instance to be called as a function,
        processing the provided query and returning the generated response.

        @param query (str): The input query to be processed by the LLM.
        @return The generated response as a string.
        """
        return self.llm.invoke(query)  # Invoke the LLM with the query and return the response
    
    def get_baseLLM(self) -> ChatOpenAI:
        """
        @brief Retrieves the base LLM instance.

        @return The ChatOpenAI instance used for generating responses.
        """
        return self.llm  # Return the initialized LLM instance