from models.base_model import BaseModel


class City(BaseModel):

    def __init__(self, city_id, name, coordinates, city_class, population, layover_size):
        self.city_id = city_id
        self.name = name
        self.coordinates = coordinates
        self.city_class = city_class
        self.population = population
        self.layover_size = layover_size
