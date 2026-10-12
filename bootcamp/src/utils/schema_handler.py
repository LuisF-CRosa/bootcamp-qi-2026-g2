import json
import os
import falcon
from jsonschema import validate, ValidationError

def validate_schema(schema_name):
    def decorator(func):
        def wrapper(self, req, resp, *args, **kwargs):
            schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", schema_name)
            try:
                with open(schema_path, "r") as f:
                    schema = json.load(f)
                
                if req.media is None:
                    raise falcon.HTTPBadRequest(title="Payload Ausente", description="O corpo da requisição não pode estar vazio.")
                
                validate(instance=req.media, schema=schema)
            except FileNotFoundError:
                raise falcon.HTTPInternalServerError(title="Erro Interno", description=f"Schema {schema_name} não encontrado.")
            except ValidationError as e:
                raise falcon.HTTPBadRequest(title="Contrato Inválido", description=e.message)
            except Exception as e:
                raise falcon.HTTPBadRequest(title="Erro de Validação", description=str(e))
                
            return func(self, req, resp, *args, **kwargs)
        return wrapper
    return decorator
