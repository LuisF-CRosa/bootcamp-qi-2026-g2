from falcon import Request, Response, HTTP_201
from src.controllers.transaction_controller import TransactionController
from src.utils.schema_handler import validate_schema

class TransactionTransferResource:
    @validate_schema("post_transfer.json")
    def on_post(self, req: Request, resp: Response):
        session = req.context.session
        payload = req.media
        idempotency_key = req.get_header("Idempotency-Key")

        controller = TransactionController(session)
        result = controller.transfer(payload, idempotency_key)

        resp.status = HTTP_201
        resp.media = result