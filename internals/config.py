"""
Contains the Config class for the application.
"""

# Standard Library Imports
from os import environ

# Third Party Imports
from dotenv import load_dotenv as loadDotEnv

# Local Imports
from .logging import createLogger, SuppressedLoggerAdapter


class Config:
    """
    Acts as a consumer of the .env file and makes it available to the application more easily whilst also providing
    default values and error handling.
    """

    # Type Hints
    logger: SuppressedLoggerAdapter
    cache: dict[str, str | int | float | bool]

    def __init__(self) -> None:
        """
        Config class constructor
        """
        # Set properties
        self.logger = createLogger(__name__)

        # Load .env file
        loadDotEnv()

        # Set properties
        self.cache = {}
        self._load()

        # Set properties
        self.logger.info("Loading .env file...")

    def _load(self) -> None:
        """
        Load the .env file.
        """
        # Load .env file
        for key, value in environ.items():
            self.cache[key] = value

        # Ensure required properties are set
        requiredProperties = [
            "DB_USER",
            "DB_PASS",
            "DB_HOST",
            "DB_PORT",
            "DB_NAME"
        ]

        for _property in requiredProperties:
            if _property not in self.cache:
                raise Exception(f"Missing required property: {_property}")

    @property
    def dbUser(self) -> str:
        """
        Database user.

        Returns:
            str: Database user.
        """
        return self.cache["DB_USER"]

    @property
    def dbPassword(self) -> str:
        """
        Database password.

        Returns:
            str: Database password.
        """
        return self.cache["DB_PASS"]

    @property
    def dbHost(self) -> str:
        """
        Database host.

        Returns:
            str: Database host.
        """
        return self.cache["DB_HOST"]

    @property
    def dbPort(self) -> int:
        """
        Database port.

        Returns:
            int: Database port.
        """
        return int(self.cache["DB_PORT"])

    @property
    def dbDatabase(self) -> str:
        """
        Database name.

        Returns:
            str: Database name.
        """
        return self.cache["DB_NAME"]

    @property
    def database(self) -> tuple[str, str, str, int, str]:
        """
        Database properties.

        Returns:
            dict[str, str]: Database properties.
        """
        return (
            self.dbUser,
            self.dbPassword,
            self.dbHost,
            self.dbPort,
            self.dbDatabase
        )

    @property
    def debug(self) -> bool:
        """
        Debug mode.

        Returns:
            bool: Debug mode.
        """
        return self.cache.get("DEBUG", "False").lower() == "true"
