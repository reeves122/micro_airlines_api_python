import logging
import os
import unittest

import moto

from src.models.player import Player
from tests import shared_test_utils

logging.basicConfig(level=logging.INFO)


class TestPlayer(unittest.TestCase):

    def setUp(self):
        """
        Initialize test http client and set up the requestContext
        :return:
        """
        # These are needed to avoid a credential error when testing
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

        from src.utils import utils
        from src.micro_airlines_api import app
        self.utils = utils
        self.assertEqual(app.debug, False)
        self.http_client = app.test_client()
        self.test_player_1 = Player(player_id='test_player_1', balance=100000)
        self.request = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.test_player_1.player_id
                    }
                }
            }
        }
        self.http_client.environ_base['awsgi.event'] = self.request

    @moto.mock_dynamodb2
    def test_player_get(self):
        """
        Test getting a player
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='test_player_1', balance=100000)
        result = self.http_client.get('/v1/player')
        self.assertEqual({'player_id': 'test_player_1', 'balance': 100000}, result.get_json())
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_player_get_not_exist(self):
        """
        Test getting a player that doesnt exist
        """
        shared_test_utils.create_table()
        result = self.http_client.get('/v1/player')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_player_post(self):
        """
        Test creating a player
        """
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/player')
        self.assertEqual('Player "test_player_1" created with balance: 100000',
                         result.get_data().decode('utf-8'))
        self.assertEqual(201, result.status_code)

    @moto.mock_dynamodb2
    def test_player_post_already_exist(self):
        """
        Test creating a player that already exists
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='test_player_1', balance=100000)
        result = self.http_client.post('/v1/player')
        self.assertEqual('Player "test_player_1" already exists', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)
