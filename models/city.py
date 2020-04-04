import time
from decimal import Decimal

from models.base_model import BaseModel


class City(BaseModel):

    def __init__(self, city_id, name, country, cost, city_class,
                 population, layover_size, latitude, longitude):
        self.city_id = city_id
        self.name = name
        self.country = country
        self.cost = cost
        self.city_class = city_class
        self.population = Decimal(str(population))
        self.layover_size = layover_size
        self.layovers = {}
        self.jobs = {}
        self.jobs_expire = int(time.time())
        self.latitude = Decimal(str(latitude))
        self.longitude = Decimal(str(longitude))
