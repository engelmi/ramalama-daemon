from marshmallow import Schema, fields

class WorkerRegistrationDTO(Schema):
    name = fields.String(required=True)
    host = fields.String(required=True)
    api_port = fields.Integer(required=True)

class WorkerUnregistrationDTO(Schema):
    name = fields.String(required=True)

class RegisteredWorkerDTO(Schema):
    name = fields.String(required=True)
    host = fields.String(required=True)
    api_port = fields.String(required=True)

class WorkerModelsDTO(Schema):
    name = fields.String(required=True)
