from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from lib.instances.instance import Instance

async def getAsyncUserDB():
    """
    @brief Asynchronously retrieves a database session for user operations.

    This function creates an asynchronous database engine and session for user-related database operations.
    It yields an AsyncSession instance to be used in FastAPI dependency injection.

    @return Yields an AsyncSession instance for user database operations.

    @exception Exception If there is an error creating the database engine or session.
    """
    instance = Instance()

    # Construct the database URL for the user database
    database_user_database_name = instance.async_database_url + "/" + instance.user_database_name
    try:
        # Create an asynchronous engine for the user database
        async_user_engine = create_async_engine(database_user_database_name, echo=False, isolation_level="AUTOCOMMIT")
        
        # Create a local sessionmaker for asynchronous sessions
        async_user_session_local = sessionmaker(bind=async_user_engine, class_=AsyncSession, expire_on_commit=False)
        
        # Yield a session for use in the context
        async with async_user_session_local() as db:
            yield db
    except Exception as e:
        # Raise an exception if there is an error connecting to the database
        raise Exception(f"Database error: {e}")

async def getAsyncDB(database_name: str):
    """
    @brief Asynchronously retrieves a database session for a specified database.

    This function creates an asynchronous database engine and session for the specified database name.
    It yields an AsyncSession instance to be used in FastAPI dependency injection.

    @param database_name The name of the database to connect to.
    @return Yields an AsyncSession instance for the specified database.

    @exception Exception If there is an error creating the database engine or session.
    """
    instance = Instance()

    # Construct the database URL for the specified database
    database_user_database_name = instance.async_database_url + "/" + database_name
    try:
        # Create an asynchronous engine for the specified database
        async_user_engine = create_async_engine(database_user_database_name, echo=False, isolation_level="AUTOCOMMIT")
        
        # Yield a connection for use in the context
        async with async_user_engine.connect() as db:
            yield db
    except Exception as e:
        # Raise an exception if there is an error connecting to the database
        raise Exception(f"Database error: {e}")