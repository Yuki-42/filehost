"""
Contains the database class for the application.
"""
from io import BytesIO

# Third Party Imports
from psycopg2 import connect, OperationalError
from passlib.hash import pbkdf2_sha512 as hashing
from psycopg2.extensions import connection as Connection, cursor as Cursor

from .config import Config
# Local Imports
from .logging import createLogger, SuppressedLoggerAdapter
from .models.file import File
from .models.user import User


class Database:
    """
    Database class for the application.
    """
    # Type Hints
    connection: Connection
    logger: SuppressedLoggerAdapter
    config: Config

    def __init__(
            self,
            config: Config
    ) -> None:
        """
        Database class constructor

        Args:
            config (Config): The application configuration.
        """
        # Set properties
        self.logger = createLogger(__name__)
        self.config = config
        self.logger.info("Creating database connection...")

        try:
            # Create connection
            self.connection = connect(
                user=config.dbUser,
                password=config.dbPassword,
                host=config.dbHost,
                port=config.dbPort,
                database=config.dbDatabase
            )
        except OperationalError as e:
            self.logger.error(f"Error creating database connection: {e}")
            raise e

        self.logger.info("Database connection created.")

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
            "INSERT INTO users(email, password, username) VALUES (%s, %s, %s) RETURNING id;",
            (
                email,
                hashedPassword,
                username,
            )
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
        cursor.execute("SELECT * FROM users WHERE id = %s;", (id,))

        # Fetch one result
        result: tuple = cursor.fetchone()
        cursor.close()

        return result is not None

    def getUserByEmail(self, email: str) -> User | None:
        """
        Get a user from the database by their email.

        Args:
            email (str): The email of the user to get.

        Returns:
            User: The user with the given email.
        """
        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))

        # Fetch one result
        result: tuple = cursor.fetchone()
        cursor.close()

        return User(*result) if result else None

    def setUserLastOtp(self, id: int, code: str) -> None:
        """
        Set the last OTP of a user in the database.

        Args:
            id (int): The id of the user.
            code (str): The OTP code to set.
        """
        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("UPDATE users SET last_otp = %s WHERE id = %s;", (code, id))

        # Commit
        self.connection.commit()
        cursor.close()

    def setUserOtpKey(self, id: int, key: str) -> None:
        """
        Set the OTP key of a user in the database.

        Args:
            id (int): The id of the user.
            key (str): The OTP key to set.
        """
        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("UPDATE users SET otp = %s WHERE id = %s;", (key, id))

        # Commit
        self.connection.commit()
        cursor.close()

    """
================================================================================================================================================================
        File
================================================================================================================================================================
    """

    def getFile(self, id: int) -> File | None:
        """
        Get a file from the database by its id.

        Args:
            id (int): The id of the file to get.

        Returns:
            File: The file with the given id.
        """

        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("SELECT * FROM files WHERE id = %s;", (id,))

        # Fetch one result
        result: tuple = cursor.fetchone()

        # Get the user
        user: User = self.getUser(result[3])

        # Get the file
        if result[5] == 1:
            cursor.execute("SELECT data FROM small_files WHERE id = %s;", (id,))
        else:
            cursor.execute("SELECT data FROM large_files WHERE id = %s;", (id,))

        file: BytesIO = BytesIO(cursor.fetchone()[0])
        cursor.close()

        return File(self.config, result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], file, user) if result else None

    def getFileByToken(self, token: str) -> File | None:
        """
        Get a file from the database by its token.

        Args:
            token (str): The token of the file to get.

        Returns:
            File: The file with the given token.
        """

        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("SELECT * FROM files WHERE token = %s;", (token,))

        # Fetch one result
        result: tuple = cursor.fetchone()

        # Get the user
        user: User = self.getUser(result[3])

        # Get the file
        if result[5] == 1:
            cursor.execute("SELECT data FROM small_files WHERE id = %s;", (result[0],))
        else:
            cursor.execute("SELECT data FROM large_files WHERE id = %s;", (result[0],))

        file: BytesIO = BytesIO(cursor.fetchone()[0])
        cursor.close()

        return File(self.config, result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], file, user) if result else None

    def getFilesByAuthor(self, userId: int) -> list[File]:
        """
        Get all files from the database by their user id.

        Args:
            userId (int): The id of the user to get files for.

        Returns:
            list: List of all files with the given user id.
        """

        # Create cursor
        cursor: Cursor = self.connection.cursor()

        # Execute query
        cursor.execute("SELECT * FROM files WHERE author_id = %s;", (userId,))

        # Fetch all results
        results: list[tuple] = cursor.fetchall()

        # Close cursor
        cursor.close()

        return [File(self.config, *result) for result in results]
