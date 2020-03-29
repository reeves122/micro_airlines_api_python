import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, request, make_response

from definitions.planes import planes
from utils import utils

blueprint = Blueprint('planes', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name='players')


@blueprint.route('/v1/planes', methods=['GET'])
def get_planes():
    """
    Get planes for a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    result = table.get_item(Key={'player_id': player_id},
                            AttributesToGet=[
                                'planes',
                            ]).get('Item')
    if not result:
        return make_response('Player does not exist', 404)

    return make_response(result.get('planes', {}), 200)


@blueprint.route('/v1/planes', methods=['POST'])
def create_plane():
    """
    Create a plane for a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    requested_plane_id = request.args.get('plane')
    if not requested_plane_id:
        return make_response('Query param "plane" is required', 400)

    plane_def = planes.get(requested_plane_id)
    if not plane_def:
        return make_response('Requested plane does not exist', 400)

    result = table.get_item(Key={'player_id': player_id},
                            AttributesToGet=[
                                'balance',
                            ]).get('Item')
    if not result:
        return make_response('Player does not exist', 404)

    player_balance = result.get('balance')
    if plane_def.cost > player_balance:
        return make_response('Player cannot afford this plane', 400)

    result = table.update_item(Key={'player_id': player_id},
                               UpdateExpression="set balance = :new_balance, "
                                                "planes.a123=:new_plane",
                               ExpressionAttributeValues={
                                    ':new_balance': 0,
                                    ':new_plane': plane_def.serialize(),
                            },
                            ReturnValues="UPDATED_NEW")
    print(result)

    return make_response('Plane added for player', 201)
