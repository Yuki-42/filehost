"""
Contains the User class.
"""

# Standard Library Imports
from datetime import datetime


class User:
    """
    User class for the application.
    """

    # Type Hints
    id: int
    email: str
    password: str
    username: str
    banned: bool
    moderator: bool
    admin: bool
    otp: str
    lastOtp: int
    createdAt: datetime

    def __init__(
            self,
            id: int,
            email: str,
            password: str,
            username: str,
            accessLevel: int,
            otp: str,
            lastOtp: int,
            createdAt: datetime
    ) -> None:
        """
        User class constructor

        Args:
            id (int): User ID.
            email (str): User email.
            password (str): User password.
            username (str): User username.
            accessLevel (int): User access level.
            otp (str): User otp.
            lastOtp (int): User last otp.
            createdAt (str): User created at.
        """

        # Set properties
        self.id = id
        self.email = email
        self.password = password
        self.username = username
        self.banned = accessLevel == -1
        self.moderator = accessLevel == 1
        self.admin = accessLevel == 2
        self.otp = otp
        self.lastOtp = lastOtp
        print(type(createdAt))
        self.createdAt = createdAt
