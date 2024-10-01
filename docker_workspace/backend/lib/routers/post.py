from fastapi import (APIRouter, Depends, HTTPException, status, Response)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lib.ai.agents.agents import SqlQueryAgent, RagQueryAgent
from lib.models.general_models import InformationResponse
from lib.models.post_models import (HumanRequest, AIResponse)
from lib.database.models.user_model import User
from lib.database.config.configuration import getAsyncUserDB
from lib.database.schemas.database_schema import (UserCreate, UserLogin)
from lib.database.securities.security import (getPasswordHash, verifyPassword)
from lib.instances.instance import instance

router = APIRouter()

@router.post(instance.signup_end_point, response_model=InformationResponse, status_code=201)
async def signup(user: UserCreate, db: AsyncSession = Depends(getAsyncUserDB)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail already registered")
    hashed_password = getPasswordHash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"informationMessage": "User successfully registered"}

@router.post(instance.login_end_point, response_model=InformationResponse)
async def login(response: Response, form_data: UserLogin, db: AsyncSession = Depends(getAsyncUserDB)):
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalars().first()
    if not user or not verifyPassword(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    session_id = await instance.redis_tool.createSession()
    await instance.memory.createMemory(session_id=session_id)
    await instance.redis_tool.updateSession(session_id=session_id, key="user_email", value=user.email)
    
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="None",
        secure=True
    )
    
    return {"informationMessage": "Login successful"}

@router.post(instance.sql_query_end_point, response_model=AIResponse)
async def sqlQuery(request: HumanRequest, session: tuple = Depends(instance.redis_tool.getSession)):
    data = request.model_dump()
    session_id, session_data = session
    
    temp_database_path = session_data.get("temp_database_path")
    if not temp_database_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    session_memory = await instance.memory.getMemory(session_id=session_id)
    sql_query_agent = SqlQueryAgent(llm=instance.llm, memory=session_memory, temp_database_path=temp_database_path, max_iteration=instance.llm_max_iteration)
    
    response = await sql_query_agent.execute(data["humanMessage"])

    await instance.redis_tool.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}

@router.post(instance.rag_query_end_point, response_model=AIResponse)
async def ragQuery(request: HumanRequest, session: tuple = Depends(instance.redis_tool.getSession)):
    data = request.model_dump()
    session_id, session_data = session
    
    vector_store_path = session_data.get("vector_store_path")
    if not vector_store_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    session_memory = await instance.memory.getMemory(session_id=session_id)
    rag_query_agent = RagQueryAgent(llm=instance.llm, memory=session_memory, vector_store_path=vector_store_path, embeddings=instance.embedding, max_iteration=instance.llm_max_iteration)
    
    response = await rag_query_agent.execute(data["humanMessage"])

    await instance.redis_tool.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}
