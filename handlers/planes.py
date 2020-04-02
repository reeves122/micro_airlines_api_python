import logging
import time

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
    logger.info(f'Received GET request from player: "{player_id}" for path: "/v1/planes"')
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
    body = request.get_json(force=True)
    logger.info(f'Received POST request from player: "{player_id}" '
                f'for path: "/v1/planes" with body: "{body}"')
    requested_plane_id = body.get('plane')
    starting_city_id = body.get('city')

    success, result = utils.add_plane_to_player(player_id=player_id, plane_id=requested_plane_id,
                                                current_city_id=starting_city_id)
    if success:
        return make_response({
            'balance': result.get('balance')
        }, 201)
    else:
        return make_response(result, 400)


@blueprint.route('/v1/planes/<string:plane_id>/depart', methods=['PUT'])
def plane_depart(plane_id):
    """
    Handle a plane departing

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    body = request.get_json(force=True)
    logger.info(f'Received PUT request from player: "{player_id}" '
                f'for path: "/v1/planes/{plane_id}" with body: "{body}"')

    success, result = utils.get_player_attributes(player_id=player_id,
                                                  attributes_to_get=['cities', 'planes'])
    if not success:
        return make_response(result, 400)

    player_cities = result.get('cities', {})
    player_plane = result.get('planes', {}).get(plane_id)

    if not player_plane:
        return make_response('Invalid plane_id', 400)

    if not any(value for _, value in body.items()):
        return make_response('No changes specified', 400)

    if not body.get('loaded_jobs') and body.get('destination_city_id'):
        return make_response('loaded_jobs and destination_city_id are required', 400)

    # Handle new jobs
    job_ids = body.get('loaded_jobs')
    source_city = player_cities.get(player_plane.get('current_city_id'))

    # Check if the plane has capacity
    if len(job_ids) > player_plane.get('capacity') - len(player_plane.get('loaded_jobs')):
        return make_response('Not enough capacity', 400)

    if time.time() > source_city.get('jobs_expire'):
        return make_response('Jobs have expired', 400)

    try:
        # Get job definitions from job ids
        jobs = {job_id: source_city['jobs'][job_id] for job_id in job_ids}
    except KeyError:
        return make_response('One or more job ids is invalid', 400)

    # Check if the jobs match the plane type (P or C)
    if any([job for job in jobs.values()
            if job.get('job_type') != player_plane.get('capacity_type')]):
        return make_response('Plane is incompatible with one or more job types', 400)

    # Combine new jobs with existing loaded jobs
    jobs = {**player_plane.get('loaded_jobs'), **jobs}

    updated, result = utils.add_jobs_to_plane_and_set_destination(player_id, plane_id, jobs,
                                                                  body.get('destination_city_id'))
    if not updated:
        return make_response(result, 400)

    utils.remove_jobs_from_city(player_id, source_city.get('city_id'), job_ids)

    return make_response('', 200)


@blueprint.route('/v1/planes/<string:plane_id>/arrive', methods=['PUT'])
def plane_arrive(plane_id):
    """
    Handle a plane arriving

    :return: API Gateway dictionary response
    """
    player_id = utils.get_username()
    success, result = utils.get_player_attributes(player_id=player_id, attributes_to_get=['planes'])
    if not success:
        return make_response(result, 400)

    player_plane = result.get('planes', {}).get(plane_id)

    landed, result = utils.handle_plane_landed(player_id, plane_id, player_plane)
    if landed:
        return make_response(result, 200)

    return make_response(result, 400)
