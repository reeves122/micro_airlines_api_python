import logging
import random
import string
import time

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from flask import request

from config import config
from models.job import Job
from models.player import Player
from definitions.cities import cities
from definitions.planes import planes

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name=config.dynamodb_players_table)
logger = logging.getLogger()


def get_username():
    username = request.environ.get('awsgi.event', {}).get('requestContext', {}).get(
        'authorizer', {}).get('claims', {}).get('cognito:username')
    if username:
        logger.info(f'Found Cognito username cognito:username: {username}')
        return username

    api_key = request.environ.get('awsgi.event', {}).get('requestContext', {}).get(
        'identity', {}).get('apiKey')
    if api_key:
        logger.info(f'Found apiKey: {api_key}')
        return api_key

    logger.error('Unable to find identity from Cognito or apiKey')
    return None


def generate_random_jobs(player_cities, current_city_id, count=30):
    logging.info(f'Generating {count} random job for city_id: {current_city_id}')
    player_city_ids = [city_id for city_id in player_cities.keys()
                       if city_id != current_city_id]

    jobs = {}

    for _ in range(count):

        job = Job(origin_city_id=current_city_id,
                  destination_city_id=random.choice(player_city_ids),
                  revenue=1000,
                  job_type=random.choice(['P', 'C']))
        jobs[job.id] = job.serialize()

    return jobs


def generate_random_string(length=20):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def create_player(player_id, balance):
    player = Player(player_id=player_id,
                    balance=balance)
    try:
        table.put_item(Item=player.serialize(),
                       ConditionExpression='attribute_not_exists(player_id)')
    except ClientError as e:
        if 'ConditionalCheckFailedException' in str(e):
            return False, f'Player "{player_id}" already exists'

    logging.info(f'Player "{player_id}" created with balance: {balance}')
    return True, f'Player "{player_id}" created with balance: {balance}'


def get_player_attributes(player_id, attributes_to_get):
    logging.info(f'Getting attributes: "{attributes_to_get}" for player: "{player_id}"')
    result = table.get_item(Key={'player_id': player_id},
                            AttributesToGet=attributes_to_get).get('Item')
    if result:
        results = {name: result.get(name) for name in attributes_to_get}
        logging.info(f'Retrieved attributes: {results}')
        return True, results
    else:
        return False, 'Player does not exist'


def add_city_to_player(player_id, city_id):
    city_object = cities.get(city_id)
    if not city_object:
        return False, 'City does not exist'

    try:
        logging.info(f'Trying to add city_id {city_id} to player: {player_id}')
        result = table.update_item(
            Key={'player_id': player_id},
            UpdateExpression=f"ADD balance :city_cost "
                             f"SET cities.{city_object.city_id} = :new_city",
            ExpressionAttributeValues={
                ':city_cost': -int(city_object.cost),
                ':new_city': city_object.serialize()
            },
            ConditionExpression=(Attr('balance').gte(city_object.cost) &
                                 Attr(f'cities.{city_object.city_id}').not_exists()),
            ReturnValues="UPDATED_NEW")

    except ClientError as e:
        logger.info(e)
        return False, 'Purchase failed'

    attributes = result.get('Attributes', {})
    logging.info(f'Successfully added city. {attributes}')
    return True, attributes


def add_plane_to_player(player_id, plane_id, current_city_id):
    plane_object = planes.get(plane_id)
    if not plane_object:
        return False, 'Plane does not exist'

    if not current_city_id:
        return False, 'Invalid city id'

    plane_object.current_city_id = current_city_id

    # Generate a unique ID for the plane since a player can have multiple of the same plane
    purchased_plane_id = generate_random_string()

    try:
        logging.info(f'Trying to add plane_id {plane_id} to player: {player_id}')
        result = table.update_item(
            Key={'player_id': player_id},
            UpdateExpression=f"ADD balance :plane_cost "
                             f"SET planes.{purchased_plane_id} = :new_plane",
            ExpressionAttributeValues={
                ':plane_cost': -int(plane_object.cost),
                ':new_plane': plane_object.serialize()
            },
            ConditionExpression=Attr('balance').gte(plane_object.cost),
            ReturnValues="UPDATED_NEW")

    except ClientError as e:
        logger.info(e)
        return False, 'Purchase failed'

    attributes = result.get('Attributes', {})
    logging.info(f'Successfully added plane. {attributes}')
    return True, attributes


def add_jobs_to_plane_and_set_destination(player_id, plane_id, list_of_jobs,
                                          destination_city_id, eta=None):
    try:
        logging.info(f'Trying to load jobs on plane "{plane_id}" for '
                     f'player {player_id}. Jobs: {list_of_jobs}. '
                     f'Destination city: {destination_city_id}')

        result = table.update_item(
            Key={'player_id': player_id},
            UpdateExpression=f"SET planes.{plane_id}.loaded_jobs = :new_jobs, "
                             f"planes.{plane_id}.destination_city_id = :destination_city_id, "
                             f"planes.{plane_id}.eta = :eta",
            ExpressionAttributeValues={
                ':new_jobs': list_of_jobs,
                ':destination_city_id': destination_city_id,
                ':eta': eta if eta else int(time.time() + 300)
            },
            ReturnValues="UPDATED_NEW")

    except ClientError as e:
        logger.info(e)
        return False, 'Failed to load jobs onto plane'

    attributes = result.get('Attributes', {})
    logging.info(f'Successfully loaded jobs. {attributes}')
    return True, attributes


def handle_plane_landed(player_id, plane_id, plane):
    if not plane.get('eta'):
        return False, 'Plane has not moved'
    if plane.get('eta') > time.time():
        return False, 'Plane has not yet landed'

    logging.info('Plane landed. Calculating revenue and clearing completed jobs')

    jobs_to_remove = [job_id for job_id, job in plane.get('loaded_jobs').items()
                      if job.get('destination_city_id') == plane.get('destination_city_id')]

    if not jobs_to_remove:
        return False, 'No jobs to remove at city'

    remove_jobs_expression = [f'planes.{plane_id}.loaded_jobs.{job},' for job in jobs_to_remove]

    total_revenue = sum([job.get('revenue') for _, job in plane.get('loaded_jobs').items()
                         if job.get('destination_city_id') == plane.get('destination_city_id')])

    logging.info(f'Revenue from {len(jobs_to_remove)} completed jobs: ${total_revenue}')

    result = table.update_item(
        Key={'player_id': player_id},
        UpdateExpression=f"ADD balance :total_revenue "
                         f"SET planes.{plane_id}.eta = 0, "
                         f"planes.{plane_id}.destination_city_id = none, "
                         f"planes.{plane_id}.current_city_id = :current_city_id "
                         f"REMOVE " + ' '.join(remove_jobs_expression),
        ExpressionAttributeValues={
            ':total_revenue': total_revenue,
            ':current_city_id': plane.get('destination_city_id')
        },
        ReturnValues="UPDATED_NEW")

    attributes = result.get('Attributes', {})
    logging.info(f'Successfully handled plane landing. {attributes}')
    return True, attributes


def update_city_with_new_jobs(player_id, city_id, player_cities):
    new_jobs = generate_random_jobs(player_cities, city_id)
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

    return new_jobs, jobs_expire


def remove_jobs_from_city(player_id, city_id, list_of_jobs):
    if not list_of_jobs:
        return False, 'No jobs to remove'
    try:
        logging.info(f'Trying to remove jobs for city "{city_id}" for '
                     f'player {player_id}. Jobs to remove: {list_of_jobs}')

        update_expressions = [f'cities.{city_id}.jobs.{job},' for job in list_of_jobs]

        result = table.update_item(
            Key={'player_id': player_id},
            UpdateExpression=f"REMOVE " + ' '.join(update_expressions),
            ReturnValues="UPDATED_NEW")

    except ClientError as e:
        logger.info(e)
        return False, 'Failed to remove jobs from city'

    attributes = result.get('Attributes', {})
    logging.info(f'Successfully removed jobs from city. {attributes}')
    return True, attributes
