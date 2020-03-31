import logging
import uuid
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from flask import Blueprint, request, make_response

from definitions.planes import planes
from utils import utils
from config import config

blueprint = Blueprint('planes', __name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(name=config.dynamodb_players_table)
logger = logging.getLogger()


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

    # Generate a unique ID for the plane since a player can have multiple of the same plane
    purchased_plane_id = str(uuid.uuid4())

    try:
        result = table.update_item(
            Key={'player_id': player_id},
            UpdateExpression=f"ADD balance :plane_cost "
                             f"SET planes.{purchased_plane_id} = :new_plane",
            ExpressionAttributeValues={
                ':plane_cost': -int(plane_def.cost),
                ':new_plane': plane_def.serialize()
            },
            ConditionExpression=Attr('balance').gte(plane_def.cost),
            ReturnValues="UPDATED_NEW")

    except ClientError as e:
        logger.info(e)
        return make_response('Purchase failed', 409)

    return make_response({
        'balance': result.get('Attributes', {}).get('balance')
    }, 201)
