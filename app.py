"""
App file for filehost project. 
"""
# Standard Library Imports
from secrets import token_urlsafe as tokenUrlSafe

# Third Party Imports
from flask import Flask, render_template as renderTemplate, Blueprint, Response, request, session, redirect, url_for as urlFor
from flask.sessions import SessionMixin
from pyotp import TOTP, random_base32 as otpKey

# Local Imports
from internals.config import Config
from internals.database import Database
from internals.logging import createLogger, SuppressedLoggerAdapter, EndpointLoggerAdapter
from internals.models.user import User

# Create App Logger
logger: SuppressedLoggerAdapter = createLogger("App")
endpointLogger: EndpointLoggerAdapter = createLogger("endpoints", adapterMode="endpoint", formatString="[%(asctime)s] [Endpoints] [%(levelname)s] %(message)s")  # Used for security log

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
    logger.debug(f"Cookie Data: {data}")

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

    if "2fa" not in data and user.otpKey != "":
        return "2FA Required"

    if "2fa" not in data and user.otpKey == "":
        return "Add 2FA"

    return "Valid"


def _verifyForm(form: dict, fields: list) -> tuple[bool, str]:
    """
    Verify that the form has all the required fields.

    Args:
        form (dict): The form to check.
        fields (list): The fields to check for.

    Returns:
        bool: If the form is valid.
    """
    # Check if the form has all the required fields
    for field in fields:
        if field not in form:
            return False, f"Missing field: {field}"

    return True, ""


@app.route("/", methods=["GET"])
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

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    logger.debug(f"Cookie Check: {cookieCheck}")

    match cookieCheck:
        case "Valid":
            return redirect(urlFor("_index"))
        case "2FA Required":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Banned":
            return redirect(urlFor("auth._auth_logout", condition="Banned"))
        case "Invalid User":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Invalid Session":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Add 2fa":
            return redirect(urlFor("auth._auth_2fa_add"))
        case "None":
            pass

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("auth/login.html")

    # Request is POST
    formFields: list = ["email", "password", "2fa"]
    formValid, formError = _verifyForm(request.form, formFields)

    if not formValid:
        return renderTemplate("auth/login.html", error=formError)

    # Get the user
    user: User = database.getUserByEmail(request.form["email"])

    # Ensure the password is correct
    if not user.checkPassword(request.form["password"]):
        return renderTemplate("auth/login.html", error="Invalid Password")

    # Remove password from memory
    request.form.pop("password")

    # Ensure the user exists
    if user is None:
        return renderTemplate("auth/login.html", error="Invalid Email")

    # Ensure the user is not banned
    if user.banned:
        return renderTemplate("auth/login.html", error="Banned")

    # Verify 2FA
    if not user.otp.verify(request.form["2fa"]) or user.lastOtp == request.form["2fa"]:
        return renderTemplate("auth/login.html", error="Invalid 2FA")

    # Set the session
    session["id"] = user.id
    session["2fa"] = True

    # Redirect to the index
    return redirect(urlFor("_index"))


@authBlueprint.route("/register", methods=["GET", "POST"])
@authBlueprint.route("/register/", methods=["GET", "POST"])
def _auth_register() -> str | Response:
    """
    The register page. This is where the user can register for an account.

    Returns:
        Response: The styled register page with the correct messages
        str: The register page
    """
    endpointLogger.logRequest(request)

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            return redirect(urlFor("_index"))
        case "2FA Required":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Banned":
            return redirect(urlFor("auth._auth_logout", condition="Banned"))
        case "Invalid User":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Invalid Session":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Add 2fa":
            return redirect(urlFor("auth._auth_logout", condition="2FA Required"))
        case "None":
            pass

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("auth/register.html")

    # Request is POST
    formFields: list = ["email", "password", "confirm-password", "username"]
    formValid, formError = _verifyForm(request.form, formFields)

    if not formValid:
        return renderTemplate("auth/register.html", error=formError)

    # Ensure the passwords match
    if request.form["password"] != request.form["confirm-password"]:
        del request.form["password"]
        del request.form["confirm-password"]
        return renderTemplate("auth/register.html", error="Passwords do not match")

    del request.form["confirm-password"]

    # Ensure the email is not already in use
    if database.getUserByEmail(request.form["email"]) is not None:
        return renderTemplate("auth/register.html", error="Email already in use")

    # Add the user to the database
    database.addUser(request.form["username"], request.form["password"], request.form["email"])

    del request.form["password"]

    # Redirect to the index
    return redirect(urlFor("auth._auth_2fa_add"))


@authBlueprint.route("/2fa/add", methods=["GET", "POST"])
@authBlueprint.route("/2fa/add/", methods=["GET", "POST"])
def _auth_2fa_add() -> str | Response:
    """
    The 2FA add page. This is where the user can add 2FA to their account.

    Returns:
        Response: The styled 2FA add page with the correct messages
        str: The 2FA add page
    """
    endpointLogger.logRequest(request)

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            return redirect(urlFor("_index"))
        case "2FA Required":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Banned":
            return redirect(urlFor("auth._auth_logout", condition="Banned"))
        case "Invalid User":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Invalid Session":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "None":
            return redirect(urlFor("auth._auth_login"))
        case "Add 2fa":
            pass

    # Handle GET first
    if request.method == "GET":
        # Create a new TOTP
        key: str = otpKey()
        url: str = TOTP(key).provisioning_uri(session["email"])

        # Set the session
        session["2fa"] = False
        session["2faKey"] = key

        return renderTemplate("auth/2fa_add.html", key=url)

    # Request is POST
    formFields: list = ["2fa"]
    formValid, formError = _verifyForm(request.form, formFields)

    if not formValid:
        return renderTemplate("auth/2fa_add.html", error=formError)

    # Verify the 2FA
    if not TOTP(session["2faKey"]).verify(request.form["2fa"], valid_window=1):
        return renderTemplate("auth/2fa_add.html", error="Invalid 2FA")

    # Set the user's 2FA key
    database.setUserOtpKey(session["id"], session["2faKey"])

    # Set the session
    session["2fa"] = True
    session.pop("2faKey")

    # Redirect to the index
    return redirect(urlFor("_index"))


@authBlueprint.route("/password/forgot", methods=["GET", "POST"])
@authBlueprint.route("/password/forgot/", methods=["GET", "POST"])
def _auth_password_forgot() -> str | Response:
    """
    The password forgot page. This is where the user can reset their password.

    Returns:
        Response: The styled password forgot page with the correct messages
        str: The password forgot page
    """
    endpointLogger.logRequest(request)

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            return redirect(urlFor("_index"))
        case "2FA Required":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Banned":
            return redirect(urlFor("auth._auth_logout", condition="Banned"))
        case "Invalid User":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "Invalid Session":
            return redirect(urlFor("auth._auth_logout", condition="Invalid session data"))
        case "None":
            pass

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("auth/password_forgot.html")

    # Request is POST
    formFields: list = ["email"]
    formValid, formError = _verifyForm(request.form, formFields)

    if not formValid:
        return renderTemplate("auth/password_forgot.html", error=formError)

    # Get the user
    user: User = database.getUserByEmail(request.form["email"])

    # Ensure the user exists
    if user is None:
        return renderTemplate("auth/password_forgot.html", error="Invalid Email")

    # Generate a new OTP
    code: str = otpKey()
    database.setUserLastOtp(user.id, code)

    # Send the email
    # emailer.sendVerificationEmail(user.email, code)

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


# Register Blueprints
app.register_blueprint(authBlueprint)

if __name__ == "__main__":
    # Run the app
    app.run()
