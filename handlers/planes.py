import logging
from flask import Blueprint, request, make_response

from utils import utils

blueprint = Blueprint('planes', __name__)
logger = logging.getLogger()


@blueprint.route('/v1/planes', methods=['GET'])
def get_planes():
    """
    Get planes for a player

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    success, result = utils.get_player_attributes(player_id=player_id,
                                                  attributes_to_get=['planes'])
    if success:
        return make_response(result, 200)
    else:
        return make_response(result, 404)


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

    success, result = utils.add_plane_to_player(player_id=player_id, plane_id=requested_plane_id)
    if success:
        return make_response({
            'balance': result.get('balance')
        }, 201)
    else:
        return make_response(result, 400)
