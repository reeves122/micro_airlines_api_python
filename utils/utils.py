import random
import string

import boto3
from botocore.exceptions import ClientError
from flask import request

from config import config
from models.job import Job
from models.player import Player

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name=config.dynamodb_players_table)


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
        return True, result
    else:
        return False, 'Player does not exist'
