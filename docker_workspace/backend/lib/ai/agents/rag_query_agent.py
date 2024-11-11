from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores.faiss import FAISS
from lib.ai.memory.memory import CustomSQLMemory
from lib.ai.llm.llm import LLM
from lib.ai.llm.embedding import Embedding

class RagQueryAgent:
    """
    @brief Handles retrieval-augmented generation (RAG) queries.

    This class utilizes a language model (LLM) and a vector store to generate
    responses based on user queries, utilizing past conversation history and
    relevant documents.

    Attributes:
    - max_iteration (int): The maximum number of iterations for processing queries.
    - memory (CustomSQLMemory): The memory instance for storing conversation context.
    - vector_store (FAISS): The vector store used for document retrieval.
    - retriever: The retriever for fetching relevant documents from the vector store.
    - llm_chain: The combined prompt template and LLM for generating responses.
    """
    
    def __init__(self, llm: LLM, memory: CustomSQLMemory, vector_store_path: str, embeddings: Embedding, max_iteration: int) -> None:
        """
        @brief Initializes the RagQueryAgent with required components.

        @param llm (LLM): The language model used for generating responses.
        @param memory (CustomSQLMemory): The memory instance for storing context.
        @param vector_store_path (str): Path to the FAISS vector store.
        @param embeddings (Embedding): The embedding model for document retrieval.
        @param max_iteration (int): The maximum number of iterations for processing.
        """
        self.max_iteration = max_iteration  # Set the maximum iteration limit
        self.memory = memory  # Store the memory instance
        
        # Load the FAISS vector store from the specified path
        self.vector_store = FAISS.load_local(vector_store_path + "/faiss", embeddings, allow_dangerous_deserialization=True)
        # Create a retriever for fetching relevant documents
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 10})
        
        # Define the prompt template for the LLM
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
                        Filter command must only be a file name.
                        Filter command must only be string, not list, not dict or not any other types.
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

        # Create a chain of prompt template, LLM, and output parser
        self.llm_chain = prompt_template | llm | StrOutputParser()
    
    async def execute(self, user_query: str) -> str:
        """
        @brief Executes the RAG query based on the user input.

        This method processes the user query for a specified number of iterations,
        utilizing memory and the vector store to generate a response.

        @param user_query (str): The input query from the user.
        @return The generated response as a string.
        """
        result = None
        filter_file_result_pair = []  # Initialize a list to store filter command results
        
        for i in range(self.max_iteration):
            # Retrieve conversation history from memory
            history = await self.getHistoryFromMemory()
            # Invoke the LLM chain with the input data
            result = await self.llm_chain.ainvoke(input={
                "file_names": self.getAvailableFiles(),
                "history": history,
                "command_result_pair": filter_file_result_pair,
                "max_iteration": self.max_iteration,
                "iteration": i,
                "input": user_query
            })
            
            if "Filter Command:" in result:
                # Extract filter command from the result
                filter_file = result.split("Filter Command:")[-1].strip()
                self.retriever.search_kwargs["filter"] = {"filename": filter_file}  # Set filter for document retrieval
                relevant_doc = await self.retriever.ainvoke(user_query)  # Retrieve relevant documents
                result = "\n\n".join([doc.page_content for doc in relevant_doc])  # Concatenate document contents
                # Store the filter command and its results
                filter_file_result_pair.append({f"Filter Command {i}": filter_file, f"Filter Command Result {i}": result})
            else:
                # Save the interaction to memory and return the result
                await self.addHistoryToMemory(user_query, filter_file_result_pair, result)
                return result
            
        # If maximum iterations reached without a valid response
        result = "Max iteration was reached."
        await self.addHistoryToMemory(user_query, filter_file_result_pair, result)
        return "I couldn't generate an answer according to your question. Please change your question and try again."
    
    async def addHistoryToMemory(self, user_query: dict, filter_file_result_pair: list, result: dict) -> None:
        """
        @brief Saves the interaction history to memory.

        This method saves the human message, command results, and AI response to the memory.

        @param user_query (dict): The user's input query.
        @param filter_file_result_pair (list): The list of command-result pairs.
        @param result (dict): The AI's response.
        """
        human_message_dict = {"human_message": user_query}  # Prepare human message dictionary
        command_result_pair_dict = {"command_result_pair_list": filter_file_result_pair}  # Prepare command-result pairs
        ai_message_dict = {"ai_message": result}  # Prepare AI message dictionary
        # Save context to memory
        self.memory.saveContext(human_message=human_message_dict, command_result_pair_dict=command_result_pair_dict, ai_message=ai_message_dict)

    async def getHistoryFromMemory(self) -> str:
        """
        @brief Retrieves the conversation history from memory.

        @return The formatted history of interactions as a string.
        """
        return self.memory.getHistory()  # Get and return history from memory
    
    def getAvailableFiles(self):
        """
        @brief Retrieves the list of available file names from the vector store.

        @return A list of unique file names.
        """
        return list(set(doc.metadata['filename'] for doc in self.vector_store.docstore._dict.values()))  # Return unique file names