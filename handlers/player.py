import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, make_response

from models.player import Player
from utils import utils
from config import config

blueprint = Blueprint('player', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name=config.dynamodb_players_table)


@blueprint.route('/v1/player', methods=['GET'])
def get_player():
    """
    Get a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    success, data = utils.get_player_attributes(player_id=player_id,
                                                attributes_to_get=['player_id'])
    if success:
        return make_response(data, 200)
    else:
        return make_response(data, 404)


@blueprint.route('/v1/player', methods=['POST'])
def create_player():
    """
    Create a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    created, message = utils.create_player(player_id, balance=100000)
    if not created:
        return make_response(message, 400)

    return make_response(message, 201)