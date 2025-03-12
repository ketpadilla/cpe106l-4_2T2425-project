import os
from flask import Flask

def create_app(test_config=None):
    """Create and configure an instance of the Flask application.

    This function initializes the Flask app, sets up configuration defaults,
    and ensures the instance folder exists. It also allows for custom test
    configurations to be passed in for testing purposes.

    Args:
        test_config (dict, optional): A dictionary containing configuration
            values for testing. If not provided, the app will load configuration
            from an instance config file (if it exists). Defaults to None.

    Returns:
        Flask: The configured Flask application instance.
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
