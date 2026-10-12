import os

import falcon

from src.database import get_db
from src.resources.transaction import TransactionTransferResource


PUBLIC_PATHS = {
    "/",
    "/health_check",
}


class InternalTokenMiddleware:
    def process_request(self, req, resp):
        """
        Protege todas as rotas privadas através
        do header INTERNAL-TOKEN.
        """

        if req.path in PUBLIC_PATHS:
            return

        expected_token = os.getenv("INTERNAL_TOKEN")

        received_token = req.get_header(
            "INTERNAL-TOKEN"
        )

        if (
            not expected_token
            or received_token != expected_token
        ):
            raise falcon.HTTPUnauthorized(
                title="Unauthorized",
                description=(
                    "INTERNAL-TOKEN ausente ou inválido."
                ),
            )


class DatabaseSessionMiddleware:
    def process_request(self, req, resp):
        """
        Cria uma sessão de banco para cada requisição.
        """
        req.context.session = get_db()()

    def process_response(
        self,
        req,
        resp,
        resource,
        req_succeeded,
    ):
        """
        Fecha a sessão após a requisição.
        """
        if hasattr(req.context, "session"):
            req.context.session.close()


class RootResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200

        resp.media = {
            "service": "bootcamp-api",
            "status": "running",
        }


class HealthCheckResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_204


application = falcon.App(
    middleware=[
        InternalTokenMiddleware(),
        DatabaseSessionMiddleware(),
    ]
)


application.add_route(
    "/",
    RootResource(),
)

application.add_route(
    "/health_check",
    HealthCheckResource(),
)

application.add_route(
    "/transaction/transfer",
    TransactionTransferResource(),
)
