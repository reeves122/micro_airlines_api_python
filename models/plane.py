from models.base_model import BaseModel


class Plane(BaseModel):

    def __init__(self, plane_id, name, cost, speed, weight, capacity_type, capacity,
                 flight_range, size_class, current_city_id='none', destination_city_id='none'):
        self.plane_id = plane_id
        self.name = name
        self.cost = cost
        self.speed = speed
        self.weight = weight
        self.capacity_type = capacity_type
        self.capacity = capacity
        self.flight_range = flight_range
        self.size_class = size_class
        self.loaded_jobs = {}
        self.current_city_id = current_city_id
        self.destination_city_id = destination_city_id
