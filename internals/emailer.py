"""
Contains the Emailer class.
"""
# Standard library imports

# Third party imports
from email.message import EmailMessage
from smtplib import SMTP_SSL
from ssl import SSLContext, create_default_context as createDefaultContext

# Project imports
from .logging import createLogger, SuppressedLoggerAdapter
from .config import Config


class Emailer:
    """
    Used for sending email notifications to users, such as email verification
    and password reset emails.
    """
    # Type Hints
    logger: SuppressedLoggerAdapter
    config: dict[str, str | int | bool]

    def __init__(self, config: Config):
        """
        Initializes the Emailer object.

        Args:
            config (Config): The Config object.
        """

        self.logger = createLogger("Emailer")
        self.config = config.email
        del config

    def _sendEmail(self, recipient, subject: str, body: str):
        """
        Sends an email to the recipient with the subject and body.
        Args:
            recipient (str): The recipient of the email.
            subject (str): The subject of the email.
            body (str): The body of the email.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """

        # Get the required values from config to reduce the amount of reads from the config file
        username: str = self.config["user"]

        # Create the email message
        em: EmailMessage = EmailMessage()
        em["From"] = username
        em["To"] = recipient
        em["subject"] = subject
        em.set_content(body)

        context: SSLContext | None = None

        if self.config["secure"]:
            context: SSLContext = createDefaultContext()

        # Connect to the SMTP server
        emailServer: SMTP_SSL = SMTP_SSL(self.config["host"], self.config["port"], context=context)

        # Login to the SMTP server
        self.logger.info("Attempting to login to email server")
        emailServer.login(username, self.config["password"])  # This will probably throw an exception if the login fails, so i need to do some testing
        self.logger.info("Successfully logged in to email server")

        # Send the email
        self.logger.info(f"Attempting to send email to {recipient}")
        emailServer.sendmail(username, recipient, em.as_string())
        self.logger.info(f"Successfully sent email to {recipient}")

        # Close the connection to the SMTP server
        emailServer.quit()

        return True

    def sendVerificationEmail(self, recipient: str, verificationCode: str) -> bool:
        """
        Sends a verification email to the recipient with the verification code.

        Args:
            recipient (str): The recipient of the email.
            verificationCode (str): The verification code to send.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        self.logger.info(f"Sending verification email to {recipient}")
        return self._sendEmail(
            recipient,
            "Email Verification",
            f"Please go to this link to verify your email: http://{self.config['host']}{':'.join(self.config['port']) if self.config['port'] != 80 else None}/auth/verify?token={verificationCode}"
        )
