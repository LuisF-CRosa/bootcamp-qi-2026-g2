import falcon
from src.resources.transaction import TransactionTransferResource
from src.database import get_db

class DatabaseSessionMiddleware:
    def process_request(self, req, resp):
        req.context.session = get_db()()

    def process_response(self, req, resp, resource, req_succeeded):
        if hasattr(req.context, "session"):
            req.context.session.close()

class HealthCheckResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_204

application = falcon.App(middleware=[DatabaseSessionMiddleware()])

# Mapeamento das Rotas
application.add_route("/health_check", HealthCheckResource())
application.add_route("/transaction/transfer", TransactionTransferResource())
