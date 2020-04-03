import logging
import os
import unittest

import moto

logging.basicConfig(level=logging.INFO)


class TestMarket(unittest.TestCase):

    def setUp(self):
        """
        Initialize test http client and set up the requestContext
        :return:
        """
        # These are needed to avoid a credential error when testing
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
    def test_market_cities_get(self):
        """
        Test getting cities
        """
        result = self.http_client.get('/v1/market/cities')
        self.assertEqual(2, len(result.get_json()['cities']))
        self.assertEqual(10000, result.get_json()['cities'][0]['cost'])
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_market_planes_get(self):
        """
        Test getting planes
        """
        result = self.http_client.get('/v1/market/planes')
        self.assertEqual(2, len(result.get_json()['planes']))
        self.assertEqual(200, result.get_json()['planes'][0]['cost'])
        self.assertEqual(200, result.status_code)
