import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, make_response, request

from models.player import Player
from definitions.cities import cities
from definitions.planes import planes
from utils import utils


blueprint = Blueprint('city', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name='players')


#def add_city_to_player(player_id, city_id):



@blueprint.route('/v1/cities', methods=['GET'])
def get_city():
    """
    Get a player

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
    Create a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()

    requested_city_id = request.args.get('city')
    if not requested_city_id:
        return make_response('Query param "city" is required', 400)

    city_def = cities.get(requested_city_id)
    if not city_def:
        return make_response('Requested city does not exist', 400)

    result = table.update_item(
        Key={'player_id': player_id},
        UpdateExpression="ADD balance :city_cost,",
        ExpressionAttributeValues={
            ':city_cost': -int(city_def.cost),
        },
        ConditionExpression=f'balance >= {city_def.cost}',
        ReturnValues="UPDATED_NEW")

    print(result)

    return make_response('City added for player', 201)

