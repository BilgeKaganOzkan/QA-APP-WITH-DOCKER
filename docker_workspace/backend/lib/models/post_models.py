from pydantic import BaseModel

class HumanRequest(BaseModel):
    humanMessage: str

class InformationResponse(BaseModel):
    informationMessage: str

class AIResponse(BaseModel):
    aiMessage: str