from fastapi import (APIRouter, Depends, HTTPException, status, Response, UploadFile, File)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession)
from sqlalchemy import (text, create_engine,select)
from sqlalchemy.orm import sessionmaker
from typing import List
from lib.config_parser.config_parser import Configuration
from lib.tools.redis import RedisTool
from lib.ai.agents.agents import SqlQueryAgent, RagQueryAgent
from lib.ai.memory.memory import CustomMemoryDict
from lib.ai.llm.llm import LLM
from lib.ai.llm.embedding import Embedding
from lib.models.post_models import (HumanRequest, InformationResponse, AIResponse)
from lib.database.models.user_model import User
from lib.database.config.configuration import getAsyncUserDB
from lib.database.schemas.database_schema import (UserCreate, UserLogin)
from lib.database.securities.security import (getPasswordHash, verifyPassword)
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
import pandas as pd
import os, asyncio, shutil, aiofiles

config = Configuration()

llm_model_name = config.getLLMModelName()
embedding_model_name = config.getEmbeddingLLMModelName()
llm_max_iteration = config.getLLMMaxIteration()
signup_end_point = config.getSignUpEndpoint()
login_end_point = config.getLoginEndpoint()
start_session_end_point = config.getStartSessionEndpoint()
upload_csv_end_point = config.getUploadCsvEndpoint()
upload_pdf_end_point = config.getUploadPdfEndpoint()
sql_query_end_point = config.getSqlQueryEndpoint()
rag_query_end_point = config.getRagQueryEndpoint()
end_session_end_point = config.getEndSessionEndpoint()
session_timeout = config.getSessionTimeout()
db_max_table_limit = config.getDbMaxTableLimit()
max_file_limit = config.getMaxFileLimit()
redis_ip = config.getRedisIP()
redis_port = config.getRedisPort()
app_ip = config.getAppIP()
app_port = config.getAppPort()

del config

active_session_list = []

memory = CustomMemoryDict()
llm = LLM(llm_model_name=llm_model_name)
embedding = Embedding(model_name=embedding_model_name).get_embedding()
redis_tool = RedisTool(memory=memory, session_timeout=session_timeout, redis_ip=redis_ip, redis_port=redis_port, session_list=active_session_list)