from fastapi import HTTPException, status
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import text
from lib.ai.memory.memory import CustomSQLMemory
from lib.ai.llm.llm import LLM
from lib.database.config.configuration import getAsyncDB

class SqlQueryAgent:
    """
    @brief Handles SQL query generation and execution based on user input.

    This class uses a language model to generate SQL commands based on user queries
    and previous conversation history, executing these commands against a PostgreSQL
    database created from uploaded CSV files.

    Attributes:
    - memory (CustomSQLMemory): The memory instance for storing context.
    - temp_database_path (str): Path to the temporary database.
    - max_iteration (int): The maximum number of iterations for processing queries.
    - llm_chain: The combined prompt template and LLM for generating SQL queries.
    """

    def __init__(self, llm: LLM, memory: CustomSQLMemory, temp_database_path: str, max_iteration: int) -> None:
        """
        @brief Initializes the SqlQueryAgent with required components.

        @param llm (LLM): The language model used for generating SQL queries.
        @param memory (CustomSQLMemory): The memory instance for storing context.
        @param temp_database_path (str): Path to the temporary database.
        @param max_iteration (int): The maximum number of iterations for processing.
        """
        self.memory = memory  # Store the memory instance
        self.temp_database_path = temp_database_path  # Store the path to the temporary database
        self.max_iteration = max_iteration  # Set the maximum iteration limit

        # Define the prompt template for the LLM
        prompt_template = PromptTemplate(
            input_variables=["table_names", "column_names", "input", "history", "command_result_pair", "iteration", "max_iteration"],
            template=("""You are a data scientist with access to a postgresql database created from one or more CSV files. \
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
                            Do not respond "Max iteration was reached."

                        Current State:

                            Current Iteration: "{iteration}"
                            User Query: "{input}"

                        Your Response:"""))

        # Create a chain of prompt template, LLM, and output parser
        self.llm_chain = prompt_template | llm | StrOutputParser()

    async def execute(self, user_query: str) -> str:
        """
        @brief Executes the SQL query based on the user input.

        This method processes the user query for a specified number of iterations,
        utilizing memory and the vector store to generate a response.

        @param user_query (str): The input query from the user.
        @return The generated response as a string.
        """
        result = None
        command_result_pair = []  # Initialize a list to store command-result pairs
        column_names = None  # Initialize column names as None

        # Retrieve the names of tables in the temporary database
        table_names = await self.runSQLQuery("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")

        if table_names:
            # Retrieve column names for each table
            for i in table_names:
                result = await self.runSQLQuery(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{i[0]}';")
                column_names = {i[0]: result}  # Store column names by table name
        else:
            # Raise an error if no datasets are uploaded
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Any dataset was not uploaded.")

        # Iterate to generate responses based on user queries
        for i in range(self.max_iteration):
            history = await self.getHistoryFromMemory()  # Retrieve conversation history from memory
            result = await self.llm_chain.ainvoke(input={
                "table_names": table_names,
                "column_names": column_names,
                "input": user_query, 
                "history": history,
                "command_result_pair": command_result_pair,
                "iteration": i + 1, 
                "max_iteration": self.max_iteration
            })
            if "SQL Query:" in result:
                # Extract the SQL query from the result
                sql_query = result.split("SQL Query:")[-1].strip()
                result = await self.runSQLQuery(sql_query)  # Execute the generated SQL query
                command_result_pair.append({f"SQL Query {i}": sql_query, f"SQL Query Result {i}": result})  # Store the command-result pair
            else:
                await self.addHistoryToMemory(user_query, command_result_pair, result)  # Save history to memory
                return result  # Return the result if it's not a SQL command

        # If maximum iterations reached without a valid response
        result = "Max iteration was reached."
        await self.addHistoryToMemory(user_query, command_result_pair, result)  # Save final state to memory
        return "I couldn't generate an answer according to your question. Please change your question and try again."
    
    async def runSQLQuery(self, sqlQuery: str) -> str:
        """
        @brief Executes a SQL query against the temporary database.

        This method runs the provided SQL query and returns the results.

        @param sqlQuery (str): The SQL query to be executed.
        @return The results of the SQL query execution.
        """
        async for db in getAsyncDB(self.temp_database_path):
            try:
                # Execute the SQL query and fetch the results
                result = await db.execute(text(sqlQuery))
                result = result.fetchall()  # Retrieve all results
                return result  # Return the results
            except Exception as e:
                return e  # Return the error if execution fails
    
    async def addHistoryToMemory(self, user_query: dict, command_result_pair_list: list, result: dict) -> None:
        """
        @brief Saves the interaction history to memory.

        This method saves the human message, command results, and AI response to the memory.

        @param user_query (dict): The user's input query.
        @param command_result_pair_list (list): The list of command-result pairs.
        @param result (dict): The AI's response.
        """
        human_message_dict = {"human_message": user_query}  # Prepare human message dictionary
        command_result_pair_dict = {"command_result_pair_list": command_result_pair_list}  # Prepare command-result pairs
        ai_message_dict = {"ai_message": result}  # Prepare AI message dictionary
        # Save context to memory
        self.memory.saveContext(human_message=human_message_dict, command_result_pair_dict=command_result_pair_dict, ai_message=ai_message_dict)

    async def getHistoryFromMemory(self) -> str:
        """
        @brief Retrieves the conversation history from memory.

        @return The formatted history of interactions as a string.
        """
        return self.memory.getHistory()  # Get and return history from memory