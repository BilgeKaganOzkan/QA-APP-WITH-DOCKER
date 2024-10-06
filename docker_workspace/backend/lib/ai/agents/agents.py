from fastapi import HTTPException, status
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores.faiss import FAISS
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession)
from lib.ai.memory.memory import CustomSQLMemory
from lib.ai.llm.llm import LLM
from lib.ai.llm.embedding import Embedding
import asyncio

class SqlQueryAgent:
    def __init__(self, llm: LLM, memory: CustomSQLMemory, db_path: str, max_iteration: int) -> None:
        self.memory = memory
        self.db_path = db_path
        self.max_iteration = max_iteration

        prompt_template = PromptTemplate(
            input_variables=["table_names", "column_names", "input", "history", "command_result_pair", "iteration", "max_iteration"],
            template=("""You are a data scientist with access to a database created from one or more CSV files. \
                      Each table in the database corresponds to a CSV file and Each table in the database is a dataset. Also, you are working in iterations.

                        Database Information:

                            Table names: "{table_names}"
                            Column names of each table: "{column_names}"

                        You also have access to the past conversation history:

                            Conversation History: "{history}"

                        In the history:

                            "HumanMessage" indicates the user's queries.
                            "SQL Queries and their results list" represents the SQL queries you executed and their results, \
                      which the user does not see.
                            "AIMessage" is your final response to the user. If "AIMessage" is "Max iteration was reached.", \
                      it means you exceeded the maximum iteration and couldn't generate final answer.

                        Your Task:

                            Use the conversation history to decide whether you need to execute a new SQL command or provide a final answer.
                            Consider that the user query may be related to past results or previous user queries. \
                      If the query relates to prior interactions, take that context into account when generating your response.
                            The user may upload more tables to database after for a while and ask questions about all tables or new tables. So, pay attention to the table names. 
                            If a new SQL command is required, generate and execute it. \
                      Your response must start with "SQL Query:" prefix and include only the SQL command.
                            If you encounter an error with your SQL command, adjust the command and attempt another one until it executes successfully.
                            If the user directly asks for a SQL query, generate the SQL command without the "SQL Query:" prefix.
                            If you have enough information to provide a final answer, \
                      do so without explicitly stating that your answer is based on previous queries and do not use "SQL Query:" prefix in your response.

                        Iteration Rules:

                            If you are beyond the first iteration, you can access the past SQL commands and results from previous iterations.
                            Past SQL Commands and Results: "{command_result_pair}"
                            You must provide a final answer by the "{max_iteration}" iteration at the latest. \
                      If you believe you have enough data to generate the final answer, \
                      you must do so before reaching the "{max_iteration}" iteration.
                            Do not response "Max iteration was reached."

                        Current State:

                            Current Iteration: "{iteration}"
                            User Query: "{input}"

                        Your Response:"""))

        self.llm_chain = prompt_template | llm | StrOutputParser()

    async def execute(self, user_query: str) -> str:
        result = None
        command_result_pair = []
        column_names = None

        table_names = await self.runSQLQuery("SELECT name FROM sqlite_master WHERE type='table';")

        if table_names:
            for i in table_names:
                result = await self.runSQLQuery(f"PRAGMA table_info({i[0]});")
                column_names = {i[0]: result}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Any dataset didn't upload.")


        for i in range(self.max_iteration):
            history = await self.getHistoryFromMemory()
            result = await self.llm_chain.ainvoke(input = {"table_names": table_names,
                                                            "column_names": column_names,
                                                            "input": user_query, 
                                                            "history": history,
                                                            "command_result_pair": command_result_pair,
                                                            "iteration": i+1, 
                                                            "max_iteration": self.max_iteration})
            
            if "SQL Query:" in result:
                sql_query = result.split("SQL Query:")[-1].strip()
                result = await self.runSQLQuery(sql_query)
                command_result_pair.append({f"SQL Query {i}": sql_query, f"SQL Query Result {i}": result})
            else:
                await self.addHistoryToMemory(user_query, command_result_pair, result)
                return result

        result = "Max iteration was reached."
        await self.addHistoryToMemory(user_query, command_result_pair, result)
        return "I couldn't generate an answer according to your question. Please change your question and try again."
    
    async def runSQLQuery(self, sqlQuery: str) -> str:
        async_db_engine = create_async_engine(self.db_path, echo=False)
        async_session = sessionmaker(async_db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            try:
                result = await session.execute(text(sqlQuery))
                result = result.fetchall()
                return result
            except Exception as e:
                return e
    
    async def addHistoryToMemory(self, user_query: dict, command_result_pair_list: list, result: dict) -> None:
        human_message_dict = {"human_message": user_query}
        command_result_pair_dict = {"command_result_pair_list": command_result_pair_list}
        ai_message_dict = {"ai_message": result}
        self.memory.saveContext(human_message=human_message_dict, command_result_pair_dict=command_result_pair_dict, ai_message=ai_message_dict, is_sql=True)

    async def getHistoryFromMemory(self) -> str:
        return self.memory.getHistory(is_sql=True)



class RagQueryAgent:
    def __init__(self, llm: LLM, memory: CustomSQLMemory, db_path: str, embeddings: Embedding, max_iteration: int) -> None:
        self.max_iteration = max_iteration
        self.memory = memory
        
        self.vector_store = FAISS.load_local(db_path + "/faiss", embeddings, allow_dangerous_deserialization=True)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 10})
            
        prompt_template = PromptTemplate(
            input_variables=["file_names", "history", "command_result_pair", "max_iteration", "iteration", "input"],
            template=("""You are an AI assistant that helps users by retrieving relevant information \
                    from a database of documents and answering their questions. Also, you are working in iterations.

                    You have access to the file names:

                        File names: "{file_names}"

                    You also have access to the past conversation history:

                        Conversation History: "{history}"

                    In the history:

                        "HumanMessage" indicates the user's queries.
                        "SQL Queries and their results list" represents the File names you executed and their results, \
                    which the user does not see.
                        "AIMessage" is your final response to the user. If "AIMessage" is "Max iteration was reached.", \
                    it means you exceeded the maximum iteration and couldn't generate final answer.

                    Your Task:

                        Use the conversation history to decide whether you need to execute a new filter command or provide a final answer.
                        Filter command must be a file name.
                        Consider that the user query may be related to past results or previous user queries. \
                    If the query relates to prior interactions, take that context into account when generating your response.
                        The user may upload more files after a while and ask questions about all files or new files. So, pay attention to the file names. 
                        If a new filter command is required, generate and execute it. \
                    Your response must start with "Filter Command:" prefix and include only the Filter command.
                        If you have enough information to provide a final answer, \
                    do so without explicitly stating that your answer is based on previous queries and do not use "Filter Command:" prefix in your response.

                    Iteration Rules:

                        If you are beyond the first iteration, you can access the past filter commands and results from previous iterations.
                        Past Filter Commands and Results: "{command_result_pair}"
                        You must provide a final answer by the "{max_iteration}" iteration at the latest. \
                        If you believe you have enough data to generate the final answer, \
                    you must do so before reaching the "{max_iteration}" iteration.
                        Do not respond with "Max iteration was reached."

                    Current State:

                        Current Iteration: "{iteration}"
                        User Query: "{input}"

                    Your Response: """)
        )

        self.llm_chain = prompt_template | llm | StrOutputParser()
    
    async def execute(self, user_query: str) -> str:
        result = None
        filter_file_result_pair = []
        
        for i in range(self.max_iteration):
            history = await self.getHistoryFromMemory()
            result = await self.llm_chain.ainvoke(input = {"file_names": self.getAvailableFiles(),
                                                            "history": history,
                                                            "command_result_pair": filter_file_result_pair,
                                                            "max_iteration": self.max_iteration,
                                                            "iteration": i,
                                                            "input": user_query})
            
            if "Filter Command:" in result:
                filter_file = result.split("Filter Command:")[-1].strip()
                self.retriever.search_kwargs["filter"] = {"filename": filter_file}
                relevant_doc = await self.retriever.aget_relevant_documents(user_query)
                result = "\n\n".join([doc.page_content for doc in relevant_doc])
                filter_file_result_pair.append({f"Filter Command {i}": filter_file, f"Filter Command Result {i}": result})
            else:
                await self.addHistoryToMemory(user_query, filter_file_result_pair, result)
                return result
            
        result = "Max iteration was reached."
        await self.addHistoryToMemory(user_query, filter_file_result_pair, result)
        return "I couldn't generate an answer according to your question. Please change your question and try again."
    
    async def addHistoryToMemory(self, user_query: dict, filter_file_result_pair: list, result: dict) -> None:
        human_message_dict = {"human_message": user_query}
        command_result_pair_dict = {"command_result_pair_list": filter_file_result_pair}
        ai_message_dict = {"ai_message": result}
        self.memory.saveContext(human_message=human_message_dict, command_result_pair_dict=command_result_pair_dict, ai_message=ai_message_dict, is_sql=True)

    async def getHistoryFromMemory(self) -> str:
        return self.memory.getHistory(is_sql=True)
    
    def getAvailableFiles(self):
        return list(set(doc.metadata['filename'] for doc in self.vector_store.docstore._dict.values()))