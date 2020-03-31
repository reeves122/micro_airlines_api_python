import logging
import os
import unittest

import moto

from definitions.planes import planes
from tests import shared_test_utils
from utils import utils

logging.basicConfig(level=logging.INFO)


class TestPlanes(unittest.TestCase):

    def setUp(self):
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
        from micro_airlines_api import app
        self.assertEqual(app.debug, False)
        self.http_client = app.test_client()
        self.player_name = 'test_player_1'
        self.request = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.player_name
                    }
                }
            }
        }
        self.http_client.environ_base['awsgi.event'] = self.request

    @moto.mock_dynamodb2
    def test_planes_get(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100000)
        utils.add_plane_to_player(player_id=self.player_name, plane_id='a1')
        result = self.http_client.get('/v1/planes')

        _, first_plane = result.get_json()['planes'].popitem()

        self.assertEqual(planes['a1'].serialize(), first_plane)
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_get_not_exist(self):
        shared_test_utils.create_table()
        result = self.http_client.get('/v1/planes')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=300)

        result = self.http_client.post('/v1/planes?plane=a1')
        self.assertEqual({
            'balance': 100
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        _, result = utils.get_player_attributes(self.player_name, attributes_to_get=['planes'])
        _, first_plane = result['planes'].popitem()
        self.assertEqual(planes['a1'].serialize(), first_plane)

    @moto.mock_dynamodb2
    def test_planes_post_multiple(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=600)

        result = self.http_client.post('/v1/planes?plane=a0')
        self.assertEqual({
            'balance': 400
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        result = self.http_client.post('/v1/planes?plane=a0')
        self.assertEqual({
            'balance': 200
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        _, result = utils.get_player_attributes(self.player_name, attributes_to_get=['planes'])
        self.assertEqual(2, len(result['planes'].keys()))

    @moto.mock_dynamodb2
    def test_planes_post_missing_arg(self):
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/planes')
        self.assertEqual('Query param "plane" is required', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_plane_not_exist(self):
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/planes?plane=foobar123')
        self.assertEqual('Plane does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_player_not_exist(self):
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/planes?plane=a0')
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_plane_cant_afford(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100)

        # Make the request and assert the response
        result = self.http_client.post('/v1/planes?plane=a0')
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)
