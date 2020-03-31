from models.base_model import BaseModel
from utils import utils


class Job(BaseModel):

    def __init__(self, origin_city_id, destination_city_id, revenue, job_type):
        self.id = utils.generate_random_string()
        self.origin_city_id = origin_city_id
        self.destination_city_id = destination_city_id
        self.revenue = revenue
        self.job_type = job_type
