from flask import request


def get_username():
    return request.environ.get('awsgi.event', {}).get('requestContext', {}).get(
        'authorizer', {}).get('claims', {}).get('cognito:username')