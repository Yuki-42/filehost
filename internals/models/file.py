"""
Contains the File class.
"""

# Standard Library Imports
from datetime import datetime
from io import BytesIO

# Local Imports
from .user import User
from ..config import Config


class File:
    """
    Represents a file.
    """

    # Type Hints
    id: int
    token: str
    name: str
    description: str
    authorId: int
    author: User
    public: bool
    fileType: int
    fileId: int
    createdAt: datetime
    file: BytesIO
    url: str

    def __init__(
            self,
            config: Config,
            id: int,
            token: str,
            name: str,
            description: str | None,
            authorId: int,
            public: bool,
            fileType: int,
            fileId: int,
            createdAt: datetime,
            file: BytesIO,
            user: User
    ) -> None:
        """
        File class constructor

        Args:
            id (int): File ID.
            token (str): File token.
            name (str): File name.
            description (str): File description.
            authorId (int): File author ID.
            public (bool): File public status.
            fileType (int): File type.
            fileId (int): File ID.
            createdAt (datetime): File created at.
            file (BytesIO): File data.
            user (User): File author.
        """

        # Set properties
        self.id = id
        self.token = token
        self.name = name
        self.description = description if description else ""
        self.authorId = authorId
        self.public = public
        self.fileType = fileType
        self.fileId = fileId
        self.createdAt = createdAt
        self.file = file
        self.author = user

        # Set URL
        self.url = f"{'https://' if config.https else 'http://'}{config.hostname}/files/{self.token}"


