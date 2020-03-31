import logging
import random
import string

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
    return request.environ.get('awsgi.event', {}).get('requestContext', {}).get(
        'authorizer', {}).get('claims', {}).get('cognito:username')


def generate_random_jobs(player_cities, current_city_id, count=30):
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

    return True, f'Player "{player_id}" created'


def get_player_attributes(player_id, attributes_to_get):
    result = table.get_item(Key={'player_id': player_id},
                            AttributesToGet=attributes_to_get).get('Item')
    if result:
        return True, {name: result.get(name) for name in attributes_to_get}
    else:
        return False, 'Player does not exist'


def add_city_to_player(player_id, city_id):
    city_object = cities.get(city_id)
    if not city_object:
        return False, 'City does not exist'

    try:
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

    return True, result.get('Attributes', {})


def add_plane_to_player(player_id, plane_id):
    plane_object = planes.get(plane_id)
    if not plane_object:
        return False, 'Plane does not exist'

    # Generate a unique ID for the plane since a player can have multiple of the same plane
    purchased_plane_id = generate_random_string()

    try:
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

    return True, result.get('Attributes', {})
