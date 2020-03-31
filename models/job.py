import uuid

from models.base_model import BaseModel


class Job(BaseModel):

    def __init__(self, origin_city_id, destination_city_id, revenue, job_type):
        self.id = str(uuid.uuid4())
        self.origin_city_id = origin_city_id
        self.destination_city_id = destination_city_id
        self.revenue = revenue
        self.job_type = job_type
