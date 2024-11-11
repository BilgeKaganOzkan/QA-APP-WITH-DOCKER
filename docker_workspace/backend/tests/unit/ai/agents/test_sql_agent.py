import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import text
from lib.ai.agents.sql_query_agent import SqlQueryAgent

class _MockInstance:
    def __init__(self):
        self.log_file_path = 'temp_path.log'
        self.async_database_url = "temp_db_url"
        self.temp_database_path = "temp_db_path"

@pytest.fixture
async def sql_agent():
    # Sets up an instance of SqlQueryAgent with mocked dependencies for testing
    memory_mock = MagicMock()
    llm_mock = AsyncMock()
    agent = SqlQueryAgent(llm=llm_mock, memory=memory_mock, temp_database_path="temp_db", max_iteration=10)
    return agent

@pytest.mark.asyncio
@patch("lib.ai.agents.sql_query_agent.SqlQueryAgent.addHistoryToMemory", return_value=AsyncMock)
@patch("lib.ai.agents.sql_query_agent.SqlQueryAgent.getHistoryFromMemory", return_value=AsyncMock)
@patch("lib.ai.agents.sql_query_agent.SqlQueryAgent.runSQLQuery", new_callable=AsyncMock)
async def test_sql_agent_execute_success(mock_sql_query, mock_get_history, mock_add_history, sql_agent):
    """
    Test the execute function for a successful SQL query execution.
    Checks if the LLM chain and SQL query execution flow is correctly followed.
    """
    sql_agent_instance = await sql_agent

    # Set up mock SQL query results to simulate returning table names, column names, and query results
    mock_sql_query.side_effect = [("table1",),  # First query returns table names
                                  [("id", "name", "age")],  # Second query returns column names
                                  [("1", "John", "30")]]  # Third query returns actual data

    # Mock LLM chain response for SQL command generation and final answer
    mock_llm_chain = AsyncMock()
    mock_llm_chain.ainvoke.side_effect = [
        "SQL Query: SELECT * FROM table1;",  # First iteration generates an SQL query
        "Here is the answer..."  # Final response
    ]
    
    # Patch the LLM chain in the agent instance
    with patch.object(sql_agent_instance, 'llm_chain', mock_llm_chain):
        user_query = "Get all records from table1"
        result = await sql_agent_instance.execute(user_query)

    # Check if LLM chain was called with the correct inputs
    mock_llm_chain.ainvoke.assert_called_with(input={'table_names': ('table1',), 
                                                     'column_names': {'t': [('id', 'name', 'age')]}, 
                                                     'input': 'Get all records from table1', 
                                                     'history': mock_get_history.return_value, 
                                                     'command_result_pair': [{'SQL Query 0': 'SELECT * FROM table1;', 'SQL Query Result 0': [('1', 'John', '30')]}], 
                                                     'iteration': 2, 
                                                     'max_iteration': 10})

    # Verify SQL queries were executed correctly
    mock_sql_query.assert_any_call("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    mock_sql_query.assert_called_with("SELECT * FROM table1;")

    # Assert final response is as expected
    assert result == "Here is the answer..."

@pytest.mark.asyncio
@patch("lib.ai.agents.sql_query_agent.SqlQueryAgent.runSQLQuery", side_effect=Exception("SQL error"))
async def test_sql_agent_execute_failure_sql_error(mock_sql_query, sql_agent):
    """
    Test for failure case when a SQL error occurs during execution.
    Ensures exception handling works as expected.
    """
    sql_agent_instance = await sql_agent
    user_query = "Get all records from table1"

    # Expecting an exception due to SQL error
    with pytest.raises(Exception) as exc_info:
        await sql_agent_instance.execute(user_query)

    # Verify that the raised exception contains "SQL error"
    assert "SQL error" in str(exc_info.value)
    mock_sql_query.assert_called_once()

@pytest.mark.asyncio
@patch("lib.ai.agents.sql_query_agent.SqlQueryAgent.runSQLQuery")
async def test_sql_agent_execute_failure_no_db_table(mock_sql_query, sql_agent):
    """
    Test execute method when no table is found in the database.
    Ensures it raises an HTTP 400 error.
    """
    mock_sql_query.return_value = None  # Simulates no table found
    sql_agent_instance = await sql_agent
    user_query = "Get all records from table1"

    # Expecting an HTTPException for missing dataset
    with pytest.raises(Exception) as exc_info:
        await sql_agent_instance.execute(user_query)

    # Check exception details for correct status and message
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Any dataset was not uploaded."
    mock_sql_query.assert_called_once()

@pytest.mark.asyncio
@patch("lib.ai.agents.sql_query_agent.SqlQueryAgent.runSQLQuery", return_value=[("table1",)])
async def test_sql_agent_failure_max_iteration_reached(mock_sql_query, sql_agent):
    """
    Test for handling the scenario where max iteration limit is reached.
    Ensures the agent returns an appropriate message when no final answer is generated.
    """
    sql_agent_instance = await sql_agent
    mock_llm_chain = AsyncMock()
    mock_llm_chain.ainvoke = AsyncMock(return_value="SQL Query: SELECT * FROM table1;")  # Mock an infinite loop scenario

    # Patch the LLM chain in the agent instance
    with patch.object(sql_agent_instance, 'llm_chain', mock_llm_chain):
        user_query = "Get all records from table1"
        result = await sql_agent_instance.execute(user_query)
    
    # Validate the result matches the expected response for max iteration limit
    assert result == "I couldn't generate an answer according to your question. Please change your question and try again."
    mock_llm_chain.ainvoke.assert_called()
    mock_sql_query.assert_called()

@pytest.mark.asyncio
@patch("lib.ai.agents.sql_query_agent.getAsyncDB", autospec=True)
async def test_sql_agent_run_sql_query_success(mock_get_async_db, sql_agent):
    """
    Test runSQLQuery method for successful execution and fetching of results.
    Ensures SQL query execution and result fetching works correctly.
    """
    sql_agent_instance = await sql_agent
    sql_query = "SELECT * FROM test_table;"

    # Mock async DB generator and database execution/fetching behavior
    mock_db = AsyncMock()
    async def get_async_db():
        yield mock_db
    mock_get_async_db.return_value = get_async_db()

    # Mock execute and fetchall to return a sample result set
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [("row1",), ("row2",)]
    mock_db.execute.return_value = mock_result

    # Execute runSQLQuery method and validate result
    result = await sql_agent_instance.runSQLQuery(sql_query)
    assert result == [("row1",), ("row2",)]
    mock_get_async_db.assert_called_once_with("temp_db")
    mock_result.fetchall.assert_called_once()

@pytest.mark.asyncio
async def test_sql_agent_add_history_to_memory_success(sql_agent):
    """
    Test addHistoryToMemory method to verify if history is saved correctly.
    Ensures the memory context is correctly updated with user query, command-result pairs, and final result.
    """
    sql_agent_instance = await sql_agent

    # Define test data for the function
    user_query = {"query": "SELECT * FROM table1"}
    command_result_pair_list = [{"SQL Query 1": "SELECT * FROM table1", "SQL Query Result 1": "result1"}]
    result = {"response": "This is the result"}

    # Call addHistoryToMemory and verify it saved data with correct arguments
    await sql_agent_instance.addHistoryToMemory(user_query, command_result_pair_list, result)
    sql_agent_instance.memory.saveContext.assert_called_once_with(
        human_message={"human_message": user_query},
        command_result_pair_dict={"command_result_pair_list": command_result_pair_list},
        ai_message={"ai_message": result},
    )

@pytest.mark.asyncio
async def test_sql_agent_get_history_from_memory_success(sql_agent):
    """
    Test getHistoryFromMemory method to ensure it retrieves history successfully.
    Confirms memory context retrieves correct SQL history.
    """
    sql_agent_instance = await sql_agent

    # Mock the memory history return value
    sql_agent_instance.memory.getHistory.return_value = "This is the SQL history"

    # Execute getHistoryFromMemory and verify the result
    result = await sql_agent_instance.getHistoryFromMemory()
    assert result == "This is the SQL history"
    sql_agent_instance.memory.getHistory.assert_called_once_with()