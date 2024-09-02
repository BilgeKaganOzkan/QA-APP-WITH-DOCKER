from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import os, sys

class Embedding:
    def __init__(self, model_name: str) -> None:
        load_dotenv()

        try:
            self.embedding = OpenAIEmbeddings(model=model_name, openai_api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(e)
            sys.exit(-1)
    
    def get_embedding(self) -> OpenAIEmbeddings:
        return self.embedding