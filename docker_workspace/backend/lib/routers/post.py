from fastapi import (APIRouter, Depends, HTTPException, status, Response)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lib.ai.agents.sql_query_agent import SqlQueryAgent
from lib.ai.agents.rag_query_agent import RagQueryAgent
from lib.models.general_models import InformationResponse
from lib.models.post_models import (HumanRequest, AIResponse)
from lib.database.models.user_model import User
from lib.database.config.configuration import getAsyncUserDB
from lib.database.schemas.database_schema import (UserCreate, UserLogin)
from lib.database.securities.security import (getPasswordHash, verifyPassword)
from lib.instances.instance import Instance

instance = Instance()

router = APIRouter()

@router.post(instance.signup_end_point, response_model=InformationResponse, status_code=201)
async def signup(user: UserCreate, db: AsyncSession = Depends(getAsyncUserDB)):
    """
    @brief Registers a new user in the system.

    This endpoint checks if the provided email is already registered.
    If not, it hashes the user's password and stores the user information in the database.
    
    @param user UserCreate object containing the user's email and password.
    @param db AsyncSession for database operations.
    @return Information message indicating successful registration.

    @exception HTTPException If the email is already registered.
    """

    # Check if the user email is already in the database
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail already registered")
    
    # Hash the user's password
    hashed_password = getPasswordHash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)

    # Add user to database
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return {"informationMessage": "User successfully registered"}

@router.post(instance.login_end_point, response_model=InformationResponse)
async def login(response: Response, form_data: UserLogin, db: AsyncSession = Depends(getAsyncUserDB)):
    """
    @brief Logs in a user and creates a session.

    This endpoint verifies the user's email and password. If valid,
    it creates a session and sets a cookie for the session ID.
    
    @param response FastAPI Response object for setting cookies.
    @param form_data UserLogin object containing email and password.
    @param db AsyncSession for database operations.
    @return Information message indicating successful login.

    @exception HTTPException If the email or password is incorrect.
    """

    # Fetch the user from the database
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalars().first()
    if not user or not verifyPassword(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create a new session for the user
    session_id = await instance.redis_tool.createSession()
    await instance.memory.createMemory(session_id=session_id)
    
    # Set a cookie for the session ID
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
    """
    @brief Executes a SQL query using the SqlQueryAgent.

    This endpoint retrieves the session's temporary database path
    and executes a SQL query through the SqlQueryAgent.
    
    @param request HumanRequest object containing the user's query.
    @param session The session data dependency for validation.
    @return AIResponse containing the response from the AI.

    @exception HTTPException If there is no database associated with the session.
    """
    data = request.model_dump()
    session_id, session_data = session
    
    # Retrieve the temporary database path from session data
    temp_database_path = session_data.get("temp_database_path")
    if not temp_database_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")

    # Get the session memory for the SQL query execution
    session_memory = await instance.memory.getMemory(session_id=session_id)
    sql_query_agent = SqlQueryAgent(llm=instance.llm, memory=session_memory, temp_database_path=temp_database_path, max_iteration=instance.llm_max_iteration)
    
    # Execute the SQL query
    response = await sql_query_agent.execute(data["humanMessage"])

    await instance.redis_tool.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}

@router.post(instance.rag_query_end_point, response_model=AIResponse)
async def ragQuery(request: HumanRequest, session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Executes a RAG query using the RagQueryAgent.

    This endpoint retrieves the session's vector store path
    and executes a RAG query through the RagQueryAgent.
    
    @param request HumanRequest object containing the user's query.
    @param session The session data dependency for validation.
    @return AIResponse containing the response from the AI.

    @exception HTTPException If there is no database associated with the session.
    """
    data = request.model_dump()
    session_id, session_data = session
    
    # Retrieve the vector store path from session data
    vector_store_path = session_data.get("vector_store_path")
    if not vector_store_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    # Get the session memory for the RAG query execution
    session_memory = await instance.memory.getMemory(session_id=session_id)

    rag_query_agent = RagQueryAgent(llm=instance.llm, memory=session_memory, vector_store_path=vector_store_path, embeddings=instance.embedding, max_iteration=instance.llm_max_iteration)

    # Execute the query    
    response = await rag_query_agent.execute(data["humanMessage"])

    await instance.redis_tool.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}