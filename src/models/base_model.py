class BaseModel:
    def serialize(self):
        return vars(self)
