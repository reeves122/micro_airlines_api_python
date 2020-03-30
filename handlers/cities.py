import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from flask import Blueprint, make_response, request

from definitions.cities import cities
from utils import utils


blueprint = Blueprint('cities', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name='players')


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
            ConditionExpression=Attr('balance').gte(city_def.cost),
            ReturnValues="UPDATED_NEW")

    except ClientError as e:
        if 'ConditionalCheckFailedException' in str(e):
            return make_response('Player has insufficient funds', 400)
        return make_response('Purchase failed', 500)

    return make_response({
        'balance': result.get('Attributes', {}).get('balance')
    }, 201)
