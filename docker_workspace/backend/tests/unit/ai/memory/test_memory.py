import pytest
from lib.ai.memory.memory import CustomSQLMemory, CustomMemoryDict

@pytest.mark.asyncio
async def test_memory_create_memory_success():
    """
    Test to verify if createMemory successfully creates a new session in memory_dict.
    Ensures that the session ID is stored with an instance of CustomSQLMemory.
    """
    memory_dict = CustomMemoryDict()
    
    session_id = "session_1"
    await memory_dict.createMemory(session_id)
    
    memory = await memory_dict.getMemory(session_id)
    
    # Check that memory instance is created and stored correctly
    assert isinstance(memory, CustomSQLMemory)
    assert session_id in memory_dict.memory_dict

@pytest.mark.asyncio
async def test_memory_get_memory_success():
    """
    Test to ensure getMemory retrieves the correct CustomSQLMemory instance.
    Ensures that a created session is correctly accessible by session ID.
    """
    memory_dict = CustomMemoryDict()
    session_id = "session_1"
    await memory_dict.createMemory(session_id)
    
    memory = await memory_dict.getMemory(session_id)
    
    # Check that memory is not None and session ID exists in memory_dict
    assert memory is not None
    assert session_id in memory_dict.memory_dict

@pytest.mark.asyncio
async def test_memory_get_memory_failure():
    """
    Test to verify getMemory creates a new session if it doesn't exist.
    Ensures getMemory automatically creates a new CustomSQLMemory instance if the session ID is missing.
    """
    memory_dict = CustomMemoryDict()
    session_id = "session_2"
    memory = await memory_dict.getMemory(session_id)

    # Check that a new memory instance is created even though the session didn't exist
    assert memory is not None
    assert session_id in memory_dict.memory_dict

@pytest.mark.asyncio
async def test_memory_delete_memory_success():
    """
    Test to verify deleteMemory removes the specified session from memory_dict.
    Ensures the session ID is no longer present in memory_dict after deletion.
    """
    memory_dict = CustomMemoryDict()
    session_id = "session_1"
    await memory_dict.createMemory(session_id)
    
    await memory_dict.deleteMemory(session_id)
    
    # Check that session ID was successfully removed
    assert session_id not in memory_dict.memory_dict

def test_memory_save_context_success():
    """
    Test to check if saveContext correctly saves human message, commands, and AI message.
    Ensures memory_data stores the saved context as expected.
    """
    memory = CustomSQLMemory()

    human_message = {"human_message": "This is a test human message"}
    command_result_pair_dict = {"command_result_pair_list": ["Command 1", "Command 2"]}
    ai_message = {"ai_message": "This is a test AI message"}

    # Save context and validate storage
    memory.saveContext(human_message, command_result_pair_dict, ai_message)
    assert len(memory.memory_data) == 1
    context_data = memory.memory_data[0]

    # Verify context data matches the inputs
    assert context_data["human_message"] == "This is a test human message"
    assert context_data["command_result_pair_list"] == ["Command 1", "Command 2"]
    assert context_data["ai_message"] == "This is a test AI message"

def test_memory_get_history_success():
    """
    Test to verify getHistory correctly formats and returns conversation history.
    Ensures returned history string includes expected messages and commands.
    """
    memory = CustomSQLMemory()

    # Define messages and save context
    human_message = {"human_message": "This is a test human message"}
    command_result_pair_dict = {"command_result_pair_list": ["Command 1", "Command 2"]}
    ai_message = {"ai_message": "This is a test AI message"}
    memory.saveContext(human_message, command_result_pair_dict, ai_message)

    # Retrieve history and check it includes expected data
    history = memory.getHistory()
    assert "HumanMessage: This is a test human message" in history
    assert "Commands and their results list: ['Command 1', 'Command 2']" in history
    assert "AIMessage: This is a test AI message" in history