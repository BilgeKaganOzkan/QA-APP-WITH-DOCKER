class CustomSQLMemory:
    def __init__(self):
        self.memory_data = []

    def saveContext(self, human_message: dict, sql_command_result_pair_dict: list, ai_message: dict) -> None:
        input_data = human_message.get("human_message", "")
        output_data = ai_message.get("ai_message", "")
        sql_command_result_pair_list = sql_command_result_pair_dict.get("sql_command_result_pair_list", [])

        self.memory_data.append({
            "human_message": input_data,
            "sql_command_result_pair_list": sql_command_result_pair_list,
            "ai_message": output_data
        })

    def getHistory(self) -> dict:        
        history = "\n\n".join(
            [
                f"HumanMessage: {item['human_message']}\nSQL Queries and their results list: {item['sql_command_result_pair_list']}\AIMessage: {item['ai_message']}"
                for item in self.memory_data
            ]
        )
        
        return history

class CustomMemoryDict:
    def __init__(self) -> None:
        self.memory_dict = {}

    async def createMemory(self, session_id: str) -> None:
        self.memory_dict[session_id] = CustomSQLMemory()

    async def getMemory(self, session_id: str) -> CustomSQLMemory:
        memory = self.memory_dict.get(session_id)
        if memory == None:
            self.createMemory(session_id=session_id)
            memory = self.memory_dict.get(session_id)

        return memory
    
    async def deleteMemory(self, session_id: str) -> None:
        if self.memory_dict.get(session_id) != None:
            del self.memory_dict[session_id]
