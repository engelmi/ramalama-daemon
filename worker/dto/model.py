from marshmallow import Schema, fields

class AvailableModelDTO(Schema):
    name = fields.String(required=True)
    size = fields.Int(required=True)
    modified = fields.Float(required=True)


class InferenceOptionsDTO(Schema):
    engine = fields.String(required=True)

class ServeOptionsDTO(Schema):
    expires_after = fields.Integer(required=True) # in minutes

class ModelServeRequestDTO(Schema):
    model = fields.String(required=True)
    inference_options = fields.Nested(InferenceOptionsDTO, required=True)
    serve_options = fields.Nested(ServeOptionsDTO, required=True)

class ModelServeResponseDTO(Schema):
    model_id = fields.String(required=True)

class ModelStopRequestDTO(Schema):
    model = fields.String(required=True)
