from pydantic import BaseModel

class HumanRequest(BaseModel):
    humanMessage: str

class AIResponse(BaseModel):
    aiMessage: str