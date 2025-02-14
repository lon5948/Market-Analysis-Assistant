from app.routes.auth import auth
from app.routes.main import main
from app.routes.report import report
from app.routes.vis import vis as vis_blueprint


def init_app(app):
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(vis_blueprint)
    app.register_blueprint(report)
