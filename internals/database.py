"""
Contains the database class for the application.
"""

# Third Party Imports
from psycopg2 import connect, sql
from passlib.hash import pbkdf2_sha512 as hashing
from psycopg2.extensions import connection as Connection, cursor as Cursor

# Local Imports
from .logging import createLogger, SuppressedLoggerAdapter
from .models.user import User


class Database:
    """
    Database class for the application.
    """
    # Type Hints
    connection: Connection
    logger: SuppressedLoggerAdapter

    def __init__(
            self,
            user: str,
            password: str,
            host: str,
            port: int,
            database: str
    ) -> None:
        """
        Database class constructor

        Args:
            user (str): Database user.
            password (str): Database password.
            host (str): Database host.
            port (int): Database port.
            database (str): Database name.
        """
        # Set properties
        self.logger = createLogger(__name__)
        self.logger.info("Creating database connection...")

        # Create connection
        self.connection = connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )

    """
================================================================================================================================================================
        Properties
================================================================================================================================================================
    """

    @property
    def users(self) -> list[User]:
        """
        Get all users from the database.

        Returns:
            list: List of all users in the database.
        """
        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("SELECT * FROM users")

        # Fetch all results
        results: list[tuple] = cursor.fetchall()

        # Close cursor
        cursor.close()

        return [User(*result) for result in results]

    """
================================================================================================================================================================
        Cryptography
================================================================================================================================================================
    """

    def addUser(self, username: str, plaintextPassword: str, email: str) -> int:
        """
        Adds a user to the database, with the given username and password and a randomly generated salt.

        Args:
            username (str): The username of the user to add
            plaintextPassword (str): The plaintext password of the user to add
            email (str): The email of the user to add

        Returns:
            int: The uid of the user that was added

        Raises:
            UserExistsError: If a user with the given email already exists
        """
        self.logger.debug(f"Adding user with username {username}")

        # Creates password hash
        hashedPassword: str = hashing.hash(plaintextPassword)
        plaintextPassword = ""  # Deletes the value of the plaintext password to prevent it from being stored in memory
        del plaintextPassword

        # Create Cursor
        cursor: Cursor = self.connection.cursor()

        # Adds the user to the database
        cursor.execute(
            "INSERT INTO users (email, password, username) VALUES (?, ?, ?) RETURNING id;",
            [
                email,
                hashedPassword,
                username
            ]
        )

        # Get the uid of the user
        uid: int = cursor.fetchone()[0]
        cursor.close()

        self.connection.commit()

        return uid

    """
================================================================================================================================================================
        User
================================================================================================================================================================
    """

    def getUser(self, id: int) -> User | None:
        """
        Get a user from the database by their id.

        Args:
            id (int): The id of the user to get.

        Returns:
            User: The user with the given id.
        """

        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("SELECT * FROM users WHERE id = %s", (id,))

        # Fetch one result
        result: tuple = cursor.fetchone()
        cursor.close()

        return User(*result) if result else None

    def checkUserExists(self, id: int) -> bool:
        """
        Check if a user exists in the database by their id.

        Args:
            id (int): The id of the user to check.

        Returns:
            bool: If the user exists.
        """
        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("SELECT * FROM users WHERE id = %s", (id,))

        # Fetch one result
        result: tuple = cursor.fetchone()
        cursor.close()

        return result is not None
