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
            "DB_NAME",
            "EMAIL_USER",
            "EMAIL_HOST",
            "EMAIL_PORT",
            "EMAIL_PASSWORD",
            "HOST_EMAIL",
            "HOST",
            "PORT",
            "DOMAIN",
            "HTTPS"
        ]

        for _property in requiredProperties:
            if _property not in self.cache:
                raise Exception(f"Missing required property: {_property}")

    @property
    def host(self) -> str:
        """
        Host ip.

        Returns:
            str: Host.
        """
        return self.cache["HOST"]

    @property
    def port(self) -> int:
        """
        Port.

        Returns:
            int: Port.
        """
        return int(self.cache["PORT"])

    @property
    def domain(self) -> str:
        """
        Hostname.

        Returns:
            str: Hostname.
        """
        return self.cache["DOMAIN"]

    @property
    def https(self) -> bool:
        """
        HTTPS.

        Returns:
            bool: HTTPS.
        """
        return self.cache.get("HTTPS", "False").lower() == "true"

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

    @property
    def email(self) -> dict[str, str | int | bool]:
        """
        Email properties.

        Returns:
            dict[str, str]: Email properties.
        """
        return {
            "user": self.emailUser,
            "host": self.emailHost,
            "port": self.emailPort,
            "secure": self.emailSecure,
            "password": self.emailPassword
        }

    @property
    def emailUser(self) -> str:
        """
        Email user.

        Returns:
            str: Email user.
        """
        return self.cache["EMAIL_USER"]

    @property
    def emailHost(self) -> str:
        """
        Email host.

        Returns:
            str: Email host.
        """
        return self.cache["EMAIL_HOST"]

    @property
    def emailPort(self) -> int:
        """
        Email port.

        Returns:
            int: Email port.
        """
        return int(self.cache["EMAIL_PORT"])

    @property
    def emailSecure(self) -> bool:
        """
        Secure email.

        Returns:
            bool: Secure email.
        """
        return self.cache.get("EMAIL_SECURE", "False").lower() == "true"

    @property
    def emailPassword(self) -> str:
        """
        Email password.

        Returns:
            str: Email password.
        """
        return self.cache["EMAIL_PASSWORD"]

    @property
    def hostEmail(self) -> str:
        """
        Host email.

        Returns:
            str: Host email.
        """
        return self.cache["HOST_EMAIL"]
