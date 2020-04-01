import logging
import time

import boto3
from flask import Blueprint, make_response, request

from config import config
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
    logger.info(f'Received GET request from player: "{player_id}" for path: "/v1/cities"')

    success, result = utils.get_player_attributes(player_id=player_id,
                                                  attributes_to_get=['cities'])
    if success:
        return make_response(result, 200)
    else:
        return make_response(result, 404)


@blueprint.route('/v1/cities', methods=['POST'])
def create_city():
    """
    Create a city for a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    body = request.get_json(force=True)
    logger.info(f'Received POST request from player: "{player_id}" '
                f'for path: "/v1/cities" with body: "{body}"')

    requested_city_id = body.get('city')

    success, result = utils.add_city_to_player(player_id=player_id, city_id=requested_city_id)
    if success:
        return make_response({
            'balance': result.get('balance')
        }, 201)
    else:
        return make_response(result, 400)


@blueprint.route('/v1/cities/<string:city_id>/jobs', methods=['GET'])
def get_player_city_jobs(city_id):
    """
    Get jobs for a player's city

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    logger.info(f'Received GET request from player: "{player_id}" '
                f'for path: "/v1/cities/{city_id}/jobs"')

    success, result = utils.get_player_attributes(player_id=player_id,
                                                  attributes_to_get=['cities'])
    if not success:
        return make_response(result, 400)

    player_cities = result.get('cities', {})
    if not player_cities or len(player_cities) < 2:
        return make_response('Player does not own enough cities', 400)

    player_city = player_cities.get(city_id)
    if not player_city:
        return make_response('Player does not own city', 400)

    if player_city.get('jobs_expire') > time.time():
        logging.info('Jobs have not expired, sending current jobs')
        return make_response({
            'jobs': player_city.get('jobs'),
            'jobs_expire': player_city.get('jobs_expire')
        }, 200)

    logging.info('Jobs have expired, generating new jobs')
    new_jobs = utils.generate_random_jobs(player_cities, city_id)
    jobs_expire = int(time.time()) + 240
    logging.info(f'Generated jobs: {new_jobs}')

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
