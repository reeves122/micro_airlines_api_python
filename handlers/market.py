import time

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from flask import Blueprint, make_response, request

from definitions.cities import cities
from definitions.planes import planes
from utils import utils


blueprint = Blueprint('market', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name='players')


@blueprint.route('/v1/market/cities', methods=['GET'])
def get_available_cities():
    """
    Get cities available

    :return: API Gateway dictionary response
    """
    cities_serialized = [city.serialize() for city_id, city in cities.items()]
    return make_response({'cities': cities_serialized}, 200)


@blueprint.route('/v1/market/planes', methods=['GET'])
def get_available_planes():
    """
    Get planes available

    :return: API Gateway dictionary response
    """
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