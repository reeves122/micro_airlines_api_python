from models.base_model import BaseModel


class Player(BaseModel):

    def __init__(self, player_id, balance=0, cities=None, planes=None):
        self.player_id = player_id
        self.balance = balance
        self.cities = cities
        self.planes = planes
