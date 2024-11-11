class CustomSQLMemory:
    """
    @brief Manages the context memory for SQL interactions.

    This class stores a list of context data including human messages,
    command results, and AI messages, allowing for tracking of the
    interactions in SQL queries.

    Attributes:
    - memory_data (list): A list that stores context dictionaries for each interaction.
    """
    
    def __init__(self):
        self.memory_data = []  # Initialize an empty list to store memory data

    def saveContext(self, human_message: dict, command_result_pair_dict: list, ai_message: dict) -> None:
        """
        @brief Saves the context of a human-AI interaction.

        This method constructs a context dictionary from the provided human message,
        command results, and AI message, then appends it to the memory data list.

        @param human_message (dict): A dictionary containing the human's message.
        @param command_result_pair_dict (list): A list of command-result pairs.
        @param ai_message (dict): A dictionary containing the AI's response message.
        @param is_sql (bool): A flag indicating whether the context is related to SQL (default: True).
        """
        input_data = human_message.get("human_message", "")  # Extract human message
        command_result_pair_list = command_result_pair_dict.get("command_result_pair_list", [])  # Extract command results
        output_data = ai_message.get("ai_message", "")  # Extract AI message
        
        # Create a context dictionary
        context_dict = {
                "human_message": input_data,
                "command_result_pair_list": command_result_pair_list,
                "ai_message": output_data
            }

        self.memory_data.append(context_dict)  # Append the context to memory data
            
    def getHistory(self) -> dict:    
        """
        @brief Retrieves the history of interactions.

        This method constructs a string representation of the memory data,
        summarizing all human messages, command results, and AI messages.

        @return A string summarizing the entire interaction history.
        """
        # Join all context items into a formatted history string
        history = "\n\n".join(
            [
                f"HumanMessage: {item['human_message']}\nCommands and their results list: {item['command_result_pair_list']}\nAIMessage: {item['ai_message']}"
                for item in self.memory_data
            ]
        )
        
        return history  # Return the constructed history string

class CustomMemoryDict:
    """
    @brief Manages multiple instances of CustomSQLMemory.

    This class stores memory instances for different sessions, allowing for
    independent memory management based on session IDs.

    Attributes:
    - memory_dict (dict): A dictionary mapping session IDs to their corresponding CustomSQLMemory instances.
    """
    
    def __init__(self) -> None:
        self.memory_dict = {}  # Initialize an empty dictionary to store memory for each session

    async def createMemory(self, session_id: str) -> None:
        """
        @brief Creates a new memory instance for a given session ID.

        This method initializes a new CustomSQLMemory instance and associates it
        with the provided session ID.

        @param session_id (str): The ID of the session for which memory is created.
        """
        self.memory_dict[session_id] = CustomSQLMemory()  # Create and store a new memory instance for the session

    async def getMemory(self, session_id: str) -> CustomSQLMemory:
        """
        @brief Retrieves the memory instance for a given session ID.

        If no memory instance exists for the specified session ID, it creates one.

        @param session_id (str): The ID of the session for which memory is retrieved.
        @return The CustomSQLMemory instance associated with the session ID.
        """
        memory = self.memory_dict.get(session_id)  # Attempt to get the existing memory for the session
        if memory is None:
            await self.createMemory(session_id=session_id)  # Create memory if it doesn't exist
            memory = self.memory_dict.get(session_id)  # Retrieve the newly created memory

        return memory  # Return the memory instance

    async def deleteMemory(self, session_id: str) -> None:
        """
        @brief Deletes the memory instance for a given session ID.

        This method removes the CustomSQLMemory instance associated with the
        specified session ID from the memory dictionary.

        @param session_id (str): The ID of the session whose memory is to be deleted.
        """
        if self.memory_dict.get(session_id) is not None:
            del self.memory_dict[session_id]  # Delete the memory instance for the session