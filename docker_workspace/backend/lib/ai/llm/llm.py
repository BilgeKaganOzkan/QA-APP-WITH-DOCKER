from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os, sys

class LLM:
    def __init__(self, llm_model_name: str) -> None:
        load_dotenv()

        try:
            self.llm = ChatOpenAI(temperature=0.0, model_name=llm_model_name, openai_api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(e)
            sys.exit(-1)
    
    def __call__(self, query: str) -> str:
        return self.llm.invoke(query)