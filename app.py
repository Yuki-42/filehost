"""
App file for filehost project. 
"""
from logging import DEBUG
# Standard Library Imports
from secrets import token_urlsafe as tokenUrlSafe

# Third Party Imports
from flask import Flask, render_template as renderTemplate, Blueprint, Response, request, session, redirect, url_for as urlFor
from flask.sessions import SessionMixin
from pyotp import TOTP, random_base32 as otpKey
from werkzeug import Response
from werkzeug.datastructures import FileStorage

# Local Imports
from internals.config import Config
from internals.database import Database
from internals.logging import createLogger, SuppressedLoggerAdapter, EndpointLoggerAdapter
from internals.models.file import File
from internals.models.user import User

# Create App Logger
logger: SuppressedLoggerAdapter = createLogger("App")
endpointLogger: EndpointLoggerAdapter = createLogger("endpoints", adapterMode="endpoint",
                                                     formatString="[%(asctime)s] [Endpoints] [%(levelname)s] %(message)s")  # Used for security log

# Create Config
config: Config = Config()

# Create Database
database: Database = Database(*config.database)

# Create Flask app
app: Flask = Flask(__name__)
app.template_folder = "templates"
app.debug = config.debug

# Set Key
app.secret_key = tokenUrlSafe(128) if not config.debug else "debug"

# Create Blueprints
infoBlueprint: Blueprint = Blueprint("info", __name__)  # Used for routes such as index and about
authBlueprint: Blueprint = Blueprint("auth", __name__, url_prefix="/auth")
filesBlueprint: Blueprint = Blueprint("files", __name__, url_prefix="/files")


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

    return "Valid"


def _canAdd2fa(data: SessionMixin) -> bool:
    """
    Check if the user can add 2FA.

    Returns:
        bool: If the user can add 2FA.
    """
    return "2fa" not in data or not data["2fa"]


def _verifyForm(form: dict, fields: list) -> tuple[bool, str, int]:
    """
    Verify that the form has all the required fields.

    Args:
        form (dict): The form to check.
        fields (list): The fields to check for.

    Returns:
        bool: If the form is valid.
    """
    # Check if the form has all the required fields.
    logger.debug(f"Form: {form}")

    # Count over the fields
    for number, field in enumerate(fields):
        if field not in form or form[field] == "":
            return False, f"Missing field: {field}", number

    return True, "", 0


@app.before_request
def _before_request() -> Response | None:
    """
    Before request function. Clears invalid sessions and logs the request.

    Returns:
        None
    """
    # Log the request
    endpointLogger.logRequest(request)

    # Protection against weirdness around static files
    if request.endpoint == "static":
        return

    # Clear invalid sessions
    if len(session) <= 0 or "id" not in session or not database.checkUserExists(session["id"]):
        session.clear()
        return

    if "2fa" not in session:
        session["2fa"] = False
        return redirect(urlFor("auth._auth_add_2fa"))

    # Get the user to perform more checks
    user: User = database.getUser(session["id"])

    logger.debug(f"Session Data: {session}")

    if user.banned:
        session.clear()
        return redirect(urlFor("auth._auth_logout", condition="Banned"))

    logger.debug(f"User: {user}")

    if user.otpKey == "":
        session["2fa"] = False
        return redirect(urlFor("auth._auth_add_2fa")) if request.endpoint != "auth._auth_add_2fa" else None


@app.after_request
def _after_request(response: Response) -> Response:
    """
    After request function. Logs the response.

    Args:
        response (Response): The response to log.

    Returns:
        Response: The response to send.
    """
    # Log the response
    # endpointLogger.logResponse(response)

    return response


"""
================================================================================================================================================================
    Info Routes
================================================================================================================================================================
"""


@infoBlueprint.route("/", methods=["GET"])
def _info_index() -> str:
    """
    Index route.
    
    Returns:
        str: Index route message.
    """
    return renderTemplate("info/index.html")


@infoBlueprint.route("/about", methods=["GET"])
def _info_about() -> str:
    """
    About route.

    Returns:
        str: About route message.
    """
    return renderTemplate("info/about.html")


@infoBlueprint.route("/contact", methods=["GET"])
def _info_contact() -> str:
    """
    Contact route.

    Returns:
        str: Contact route message.
    """
    return renderTemplate("info/contact.html")


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

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    logger.debug(f"Cookie Check: {cookieCheck}")

    match cookieCheck:
        case "Valid":
            return redirect(urlFor("info._info_index"))  # Logged-in users cannot access the login page
        case "None":
            pass

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("auth/login.html")

    # Request is POST
    formFields: list = ["email", "password", "2fa"]
    formValid, formError, errorNumber = _verifyForm(request.form, formFields)

    if not formValid and errorNumber != 2:
        return renderTemplate("auth/login.html", error=formError)

    # Get the user
    user: User = database.getUserByEmail(request.form["email"])

    # Ensure the user exists
    if user is None:
        return renderTemplate("auth/login.html", error="Invalid Email")

    # Check if the user has 2FA enabled
    if user.otpKey == "" and errorNumber == 2:
        session["id"] = user.id
        session["2fa"] = False
        return redirect(urlFor("auth._auth_add_2fa"))

    # Ensure the password is correct
    if not user.checkPassword(request.form["password"]):
        return renderTemplate("auth/login.html", error="Invalid Password")

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
    return redirect(urlFor("info._info_index"))


@authBlueprint.route("/register", methods=["GET", "POST"])
@authBlueprint.route("/register/", methods=["GET", "POST"])
def _auth_register() -> str | Response:
    """
    The register page. This is where the user can register for an account.

    Returns:
        Response: The styled register page with the correct messages
        str: The register page
    """

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            return redirect(urlFor("info._info_index"))  # Logged-in users cannot access the register page
        case "None":
            pass

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("auth/register.html")

    # Request is POST
    formFields: list = ["email", "password", "confirm-password", "username"]
    formValid, formError, errorNumber = _verifyForm(request.form, formFields)

    if not formValid:
        return renderTemplate("auth/register.html", error=formError)

    # Ensure the passwords match
    if request.form["password"] != request.form["confirm-password"]:
        del request.form["password"]
        del request.form["confirm-password"]
        return renderTemplate("auth/register.html", error="Passwords do not match")

    # Ensure the email is not already in use
    if database.getUserByEmail(request.form["email"]) is not None:
        return renderTemplate("auth/register.html", error="Email already in use")

    # Add the user to the database
    database.addUser(request.form["username"], request.form["password"], request.form["email"])

    # Sign the user in and redirect to 2fa add
    user: User = database.getUserByEmail(request.form["email"])
    session["id"] = user.id

    # Redirect to the index
    return redirect(urlFor("auth._auth_add_2fa"))


@authBlueprint.route("/2fa/add", methods=["GET", "POST"])
@authBlueprint.route("/2fa/add/", methods=["GET", "POST"])
def _auth_add_2fa() -> str | Response:
    """
    The 2FA add page. This is where the user can add 2FA to their account.

    Returns:
        Response: The styled 2FA add page with the correct messages
        str: The 2FA add page
    """

    # Ensure user is logged in
    if not _canAdd2fa(session):
        return redirect(urlFor("auth._auth_login"))

    # Handle GET first
    if request.method == "GET":
        # Create a new TOTP
        key: str = otpKey()
        url: str = TOTP(key).provisioning_uri(database.getUser(session["id"]).email, issuer_name="Filehost")

        # Set the session
        session["2faKey"] = key

        return renderTemplate("auth/2fa_add.html", key=url)

    # Request is POST
    formFields: list = ["2fa"]
    formValid, formError, errorNumber = _verifyForm(request.form, formFields)

    if not formValid:
        return renderTemplate("auth/2fa_add.html", error=formError)

    # Verify the 2FA
    if (not TOTP(session["2faKey"]).verify(request.form["2fa"], valid_window=1)) and (app.debug and request.form["2fa"] != "123456"):
        return renderTemplate("auth/2fa_add.html", error="Invalid 2FA")

    # Set the user's 2FA key
    database.setUserOtpKey(session["id"], session["2faKey"])

    # Set the session
    session["2fa"] = True
    session.pop("2faKey")

    # Redirect to the index
    return redirect(urlFor("info._info_index"))


@authBlueprint.route("/password/reset", methods=["GET", "POST"])
@authBlueprint.route("/password/reset/", methods=["GET", "POST"])
def _auth_password_reset() -> str | Response:
    """
    The password reset page. This is where the user can reset their password.

    Returns:
        Response: The styled password reset page with the correct messages
        str: The password reset page
    """

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            return redirect(urlFor("info._info_index"))
        case "None":
            pass

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("auth/password_reset.html")

    # Request is POST
    formFields: list = ["email"]
    formValid, formError, errorNumber = _verifyForm(request.form, formFields)

    if not formValid:
        return renderTemplate("auth/password_reset.html", error=formError)

    # Get the user
    user: User = database.getUserByEmail(request.form["email"])

    # Ensure the user exists
    if user is None:
        return renderTemplate("auth/password_reset.html", error="Invalid Email")

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

    # Clear the session
    session.clear()

    # Redirect to the index
    return renderTemplate("auth/logout.html", condition=condition)


@filesBlueprint.route("/upload", methods=["GET", "POST"])
@filesBlueprint.route("/upload/", methods=["GET", "POST"])
def _files_upload() -> str | Response:
    """
    The upload page. This is where the user can upload files to their account.

    Returns:
        Response: The styled upload page with the correct messages
        str: The upload page
    """

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            pass
        case "None":
            return redirect(urlFor("auth._auth_login"))

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("files/upload.html")

    # Request is POST
    formFields: list = ["file"]

    if "file" not in request.files:
        return renderTemplate("files/upload.html", error="No file uploaded")

    file: FileStorage = request.files["file"]


@filesBlueprint.route("/upload/bulk", methods=["GET", "POST"])
@filesBlueprint.route("/upload/bulk/", methods=["GET", "POST"])
def _files_upload_bulk() -> str | Response:
    """
    The bulk upload page. This is where the user can upload multiple files to their account.

    Returns:
        Response: The styled bulk upload page with the correct messages
        str: The bulk upload page
    """

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            pass
        case "None":
            return redirect(urlFor("auth._auth_login"))

    # Handle GET first
    if request.method == "GET":
        return renderTemplate("files/upload.html", bulk=True)

    # Request is POST
    formFields: list = ["files"]

    if "files" not in request.files:
        return renderTemplate("files/upload.html", bulk=True, error="No files uploaded")  # TODO: finish this


@filesBlueprint.route("/<string:file>", methods=["GET"])
@filesBlueprint.route("/<string:file>/", methods=["GET"])
def _files_get(file: str) -> str | Response:
    """
    The file page. This is where the user can view a file.

    Args:
        file (str): The file to view.

    Returns:
        Response: The styled file page with the correct messages
        str: The file page
    """

    # Hande cookie check
    cookieCheck: str = _cookieCheck(session)

    match cookieCheck:
        case "Valid":
            pass
        case "None":
            return redirect(urlFor("auth._auth_login"))

    # Get the file
    fileData: File = database.getFileByToken(file)

    if fileData is None:
        return renderTemplate("files/file.html", error="File not found")

    return renderTemplate("files/file.html", file=fileData)


@app.route("/test/<string:template>")
def _test(template: str) -> str:
    """
    Test route for testing templates.

    Args:
        template (str): The template to test.

    Returns:
        str: The rendered template.
    """
    return renderTemplate(f"auth/{template}.html")


# Register Blueprints
app.register_blueprint(infoBlueprint)
app.register_blueprint(authBlueprint)
app.register_blueprint(filesBlueprint)

if __name__ == "__main__":
    # Run the app
    app.run()
