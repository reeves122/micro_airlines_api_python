import logging

import boto3
from flask import Blueprint, make_response

from definitions.cities import cities
from definitions.planes import planes
from config import config

blueprint = Blueprint('market', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name=config.dynamodb_players_table)
logger = logging.getLogger()


@blueprint.route('/v1/market/cities', methods=['GET'])
def get_available_cities():
    """
    Get cities available

    :return: API Gateway dictionary response
    """
    logger.info(f'Received GET request for path: "/v1/market/cities"')
    cities_serialized = [city.serialize() for city_id, city in cities.items()]
    response = make_response({'cities': cities_serialized}, 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@blueprint.route('/v1/market/planes', methods=['GET'])
def get_available_planes():
    """
    Get planes available

    :return: API Gateway dictionary response
    """
    logger.info(f'Received GET request for path: "/v1/market/planes"')
    # TODO: Implement time-based market for planes
    # player_id = utils.get_username()
    #
    # result = table.get_item(Key={'player_id': player_id},
    #                         AttributesToGet=[
    #                             'market_planes',
    #                         ]).get('Item')
    # if not result:
    #     return make_response('Player does not exist', 404)
    #
    # market_planes = result.get('market_planes', {})
    # if not market_planes or market_planes.get('expires', 0) > time.time():
    #     market_planes = {
    #
    #     }
    #
    # make_response(market_planes, 200)

    planes_serialized = [plane.serialize() for plane_id, plane in planes.items()]
    return make_response({'planes': planes_serialized}, 200)
