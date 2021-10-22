import logging

import boto3
from flask import Blueprint, make_response

from utils import utils
from config import config

blueprint = Blueprint('player', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name=config.dynamodb_players_table)
logger = logging.getLogger()


@blueprint.route('/v1/player', methods=['GET'])
def get_player():
    """
    Get a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    logger.info(f'Received GET request from player: "{player_id}" for path: "/v1/player"')

    success, result = utils.get_player_attributes(player_id=player_id,
                                                  attributes_to_get=['player_id', 'balance'])
    if success:
        return make_response(result, 200)
    else:
        return make_response(result, 404)


@blueprint.route('/v1/player', methods=['POST'])
def create_player():
    """
    Create a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    logger.info(f'Received POST request from player: "{player_id}" '
                f'for path: "/v1/player"')

    created, message = utils.create_player(player_id, balance=100000)
    if not created:
        return make_response(message, 400)

    return make_response(message, 201)
