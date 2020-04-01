import logging
import os
import unittest

import moto

from models.player import Player
from utils import utils
from tests import shared_test_utils

logging.basicConfig(level=logging.INFO)


class TestPlayer(unittest.TestCase):

    def setUp(self):
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
        from micro_airlines_api import app
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
        shared_test_utils.create_table()
        utils.create_player(player_id='test_player_1', balance=100000)
        result = self.http_client.get('/v1/player')
        self.assertEqual({'player_id': 'test_player_1'}, result.get_json())
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_player_get_not_exist(self):
        shared_test_utils.create_table()
        result = self.http_client.get('/v1/player')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_player_post(self):
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/player')
        self.assertEqual('Player "test_player_1" created with balance: 100000',
                         result.get_data().decode('utf-8'))
        self.assertEqual(201, result.status_code)

    @moto.mock_dynamodb2
    def test_player_post_already_exist(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='test_player_1', balance=100000)
        result = self.http_client.post('/v1/player')
        self.assertEqual('Player "test_player_1" already exists', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)
