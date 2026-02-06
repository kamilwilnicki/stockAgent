from flask import Flask
from app.controllers.routes import api
import os
from dotenv import load_dotenv
load_dotenv()



def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(api)
    return app


if __name__=="__main__":
    app = create_app()
    port = 8080
    app.run(debug=True, port=port)