from models.base_model import BaseModel


class Player(BaseModel):

    def __init__(self, player_id):
        self.player_id = player_id
        self.balance = 0
