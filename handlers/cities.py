import logging
import time

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from flask import Blueprint, make_response, request

from config import config
from definitions.cities import cities
from utils import utils

blueprint = Blueprint('cities', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name=config.dynamodb_players_table)
logger = logging.getLogger()


@blueprint.route('/v1/cities', methods=['GET'])
def get_player_cities():
    """
    Get cities for a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    result = table.get_item(Key={'player_id': player_id},
                            AttributesToGet=[
                                'cities',
                            ]).get('Item')
    if not result:
        return make_response('Player does not exist', 404)

    return make_response(result.get('cities', {}), 200)


@blueprint.route('/v1/cities', methods=['POST'])
def create_city():
    """
    Create a city for a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    requested_city_id = request.args.get('city')
    if not requested_city_id:
        return make_response('Query param "city" is required', 400)

    city_def = cities.get(requested_city_id)
    if not city_def:
        return make_response('Requested city does not exist', 400)

    try:
        result = table.update_item(
            Key={'player_id': player_id},
            UpdateExpression=f"ADD balance :city_cost "
                             f"SET cities.{city_def.city_id} = :new_city",
            ExpressionAttributeValues={
                ':city_cost': -int(city_def.cost),
                ':new_city': city_def.serialize()
            },
            ConditionExpression=(Attr('balance').gte(city_def.cost) &
                                 Attr(f'cities.{city_def.city_id}').not_exists()),
            ReturnValues="UPDATED_NEW")

    except ClientError as e:
        logger.info(e)
        return make_response('Purchase failed', 409)

    return make_response({
        'balance': result.get('Attributes', {}).get('balance')
    }, 201)


@blueprint.route('/v1/cities/<string:city_id>/jobs', methods=['GET'])
def get_player_city_jobs(city_id):
    """
    Get jobs for a player's city

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    result = table.get_item(Key={'player_id': player_id},
                            AttributesToGet=[
                                'cities',
                            ]).get('Item')
    if not result:
        return make_response('Player does not exist', 404)

    player_cities = result.get('cities', {})
    if not player_cities or len(player_cities) < 2:
        return make_response('Player does not own enough cities', 400)

    player_city = player_cities.get(city_id)
    if not player_city:
        return make_response('Player does not own city', 400)

    if player_city.get('jobs', {}).get('expires', 0) > time.time():
        return make_response({
            'balance': player_city.get('jobs')
        }, 200)

    new_jobs = utils.generate_random_jobs(player_cities, city_id)
    jobs_expire = int(time.time()) + 240

    table.update_item(
        Key={'player_id': player_id},
        UpdateExpression=f"SET cities.{city_id}.jobs = :new_jobs, "
                         f"cities.{city_id}.jobs_expire = :jobs_expire",
        ExpressionAttributeValues={
            ':new_jobs': new_jobs,
            ':jobs_expire': jobs_expire
        },
        ReturnValues="UPDATED_NEW")

    return make_response({
        'new_jobs': new_jobs,
        'jobs_expire': jobs_expire
    }, 200)
