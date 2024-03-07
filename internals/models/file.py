"""
Contains the File class.
"""

# Standard Library Imports
from datetime import datetime
from io import BytesIO

# Local Imports
from .user import User


class File:
    """
    Represents a file.
    """

    # Type Hints
    id: int
    name: str
    description: str
    authorId: int
    author: User
    public: bool
    fileType: int
    fileId: int
    createdAt: datetime
    file: BytesIO

    def __init__(
            self,
            id: int,
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
        self.name = name
        self.description = description
        self.authorId = authorId
        self.public = public
        self.fileType = fileType
        self.fileId = fileId
        self.createdAt = createdAt
        self.file = file
        self.author = user
