from app.routes.auth import auth
from app.routes.main import main

def init_app(app):
    app.register_blueprint(auth)
    app.register_blueprint(main)
