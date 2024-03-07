"""
App file for filehost project. 
"""
# Standard Library Imports
from secrets import token_urlsafe as tokenUrlSafe

# Third Party Imports
from flask import Flask, render_template as renderTemplate, Blueprint, Response, request, session
from flask_wtf import CSRFProtect
from flask.sessions import SessionMixin

# Local Imports
from internals.config import Config
from internals.database import Database
from internals.logging import createLogger, SuppressedLoggerAdapter, EndpointLoggerAdapter
from internals.models.user import User

# Create App Logger
logger: SuppressedLoggerAdapter = createLogger(__name__)
endpointLogger: EndpointLoggerAdapter = createLogger("endpoints", adapterMode="endpoint")  # Used for security log

# Create Config
config: Config = Config()

# Create Database
database: Database = Database(*config.database)

# Create Flask app
app: Flask = Flask(__name__)
app.template_folder = "templates"

# Set Key
app.secret_key = tokenUrlSafe(128) if not config.debug else "debug"

# Create Blueprints
authBlueprint: Blueprint = Blueprint("auth", __name__, url_prefix="/auth")


def _cookieCheck(data: SessionMixin) -> str:
    """
    Check if the user has a valid cookie.

    Returns:
        str: The status of the user's cookie.
    """

    # TODO: Convert this to use integers instead of strings before production
    if len(data) == 0:
        return "None"

    if "id" not in data:
        return "Invalid Session"

    if not database.checkUserExists(data["id"]):
        return "Invalid User"

    user: User = database.getUser(data["id"])

    if user.banned:
        return "Banned"

    if "2fa" not in data and user.otp != "":
        return "2FA Required"

    return "Valid"


@app.route("/")
def _index() -> str:
    """
    Index route.
    
    Returns:
        str: Index route message.
    """
    return renderTemplate("index.html")


"""
================================================================================================================================================================
    Auth Routes
================================================================================================================================================================
"""


@authBlueprint.route("/login", methods=["GET", "POST"])
@authBlueprint.route("/login/", methods=["GET", "POST"])
def _auth_login() -> str | Response:
    """
    The login page. This is where the user can log in to their account.

    Returns:
        Response: The styled login page with the correct messages
        str: The login page
    """
    endpointLogger.logRequest(request)

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("auth/login.html")


@authBlueprint.route("/logout", methods=["GET"])
@authBlueprint.route("/logout/", methods=["GET"])
def _auth_logout(condition: str | None = None) -> str:
    """
    The logout page. This is where the user can log out of their account.

    Returns:
        Response: The styled logout page with the correct messages
    """
    endpointLogger.logRequest(request)

    # Clear the session
    session.clear()

    # Redirect to the index
    return renderTemplate("auth/logout.html", condition=condition)


if __name__ == "__main__":
    # Register Blueprints
    app.register_blueprint(authBlueprint)

    # Create CSRF Protection
    csrf: CSRFProtect = CSRFProtect(app)

    # Run the app
    app.run()
