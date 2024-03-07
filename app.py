"""
App file for filehost project. 
"""

# Third Party Imports
from flask import Flask, render_template as renderTemplate, Blueprint

# Local Imports
from internals.logging import createLogger

# Create App Logger
logger = createLogger(__name__)

# Create Flask app
app: Flask = Flask(__name__)


@app.route("/")
def _index() -> str:
    """
    Index route.
    
    Returns:
        str: Index route message.
    """
    return renderTemplate("index.html")


if __name__ == "__main__":
    app.run()
