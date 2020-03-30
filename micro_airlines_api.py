import logging

import awsgi
import aws_lambda_logging
from flask import Flask

from _version import __version__
from handlers import planes, player, cities, market

LOGGER = logging.getLogger()
app = Flask(__name__)
app.register_blueprint(cities.blueprint)
app.register_blueprint(market.blueprint)
app.register_blueprint(planes.blueprint)
app.register_blueprint(player.blueprint)


def lambda_handler(event, context):
    """
    AWS lambda insertion point.

    :param event: AWS Lambda event data
    :param context: AWS Lambda context
    :return: Service response
    """
    aws_lambda_logging.setup(level='INFO', boto_level='INFO')
    LOGGER.info(f'Micro Airlines API {__version__}')
    LOGGER.info({'event': event})
    return awsgi.response(app, event, context)


if __name__ == '__main__':
    # Entry point for local development
    app.run()
