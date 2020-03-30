import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, make_response

from models.player import Player
from utils import utils


blueprint = Blueprint('player', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name='players')


@blueprint.route('/v1/player', methods=['GET'])
def get_player():
    """
    Get a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    result = table.get_item(Key={'player_id': player_id},
                            AttributesToGet=[
                                'player_id',
                            ]).get('Item')
    if result:
        return make_response(result, 200)
    else:
        return make_response('Player does not exist', 404)


@blueprint.route('/v1/player', methods=['POST'])
def create_player():
    """
    Create a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    player = Player(player_id=player_id,
                    balance=100000)
    try:
        table.put_item(Item=player.serialize(),
                       ConditionExpression='attribute_not_exists(player_id)')
    except ClientError as e:
        if 'ConditionalCheckFailedException' in str(e):
            return make_response('Player already exists', 400)

    return make_response('Player created', 201)