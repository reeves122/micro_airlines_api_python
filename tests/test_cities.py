import logging
import os
import unittest
import time

import moto

from definitions.cities import cities
from utils import utils
from tests import shared_test_utils

logging.basicConfig(level=logging.INFO)


class TestCities(unittest.TestCase):

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
    def test_cities_get(self):
        """
        Test getting cities
        """
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100000)
        utils.add_city_to_player(player_id=self.player_name, city_id='c1001')

        result = self.http_client.get('/v1/cities')
        self.assertEqual({
            'cities': {
                'c1001': cities['c1001'].serialize()
            }
        }, result.get_json())
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_get_player_not_exist(self):
        """
        Test getting cities when player does not exist
        """
        shared_test_utils.create_table()
        result = self.http_client.get('/v1/cities')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post(self):
        """
        Test creating a city
        """
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=11000)

        # Make the request and assert the response
        result = self.http_client.post('/v1/cities', json={'city': 'c1001'})
        self.assertEqual({
            'balance': 1000
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        result = utils.table.get_item(Key={'player_id': self.player_name}).get('Item')
        self.assertEqual(cities['a0'].serialize(), result['cities']['c1001'])

    @moto.mock_dynamodb2
    def test_cities_post_missing_body(self):
        """
        Test creating a city when body is missing
        """
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/cities')
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_city_not_exist(self):
        """
        Test creating a city when city id does not exist
        """
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/cities?city', json={'city': 'foobar123'})
        self.assertEqual('City does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_player_not_exist(self):
        """
        Test creating a city when player does not exist
        """
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/cities', json={'city': 'a0'})
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_city_cant_afford(self):
        """
        Test creating a city when player cant afford it
        """
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=1000)

        # Make the request and assert the response
        result = self.http_client.post('/v1/cities', json={'city': 'a0'})
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_city_already_owned(self):
        """
        Test creating a city when player already owns it
        """
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100000)

        # Purchase the city first
        result = self.http_client.post('/v1/cities', json={'city': 'a0'})
        self.assertEqual(201, result.status_code)

        # Try to purchase the same city again
        result = self.http_client.post('/v1/cities', json={'city': 'a0'})
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_get_player_city_jobs(self):
        """
        Test getting jobs for a city
        """
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100000)
        utils.add_city_to_player(player_id=self.player_name, city_id='a1')
        utils.add_city_to_player(player_id=self.player_name, city_id='a2')
        utils.add_city_to_player(player_id=self.player_name, city_id='a3')
        utils.add_city_to_player(player_id=self.player_name, city_id='a4')

        result = self.http_client.get('/v1/cities/a1/jobs')
        self.assertEqual(200, result.status_code)
        self.assertEqual(30, len(result.get_json()['jobs']))
        jobs_expire = result.get_json()['jobs_expire']
        self.assertLess(time.time(), jobs_expire)

        # Make the same call again to see if cached jobs are used
        result = self.http_client.get('/v1/cities/a1/jobs')
        self.assertEqual(jobs_expire, result.get_json()['jobs_expire'])

    @moto.mock_dynamodb2
    def test_get_player_city_jobs_not_owned(self):
        """
        Test getting jobs for a city when the city is not owned
        """
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100000)
        utils.add_city_to_player(player_id=self.player_name, city_id='a1')
        utils.add_city_to_player(player_id=self.player_name, city_id='a3')

        result = self.http_client.get('/v1/cities/a2/jobs')
        self.assertEqual(400, result.status_code)
        self.assertEqual('Player does not own city', result.get_data().decode('utf-8'))

    @moto.mock_dynamodb2
    def test_get_player_city_jobs_not_enough(self):
        """
        Test getting jobs for a city when player only has one city
        """
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100000)
        utils.add_city_to_player(player_id=self.player_name, city_id='a1')

        result = self.http_client.get('/v1/cities/a1/jobs')
        self.assertEqual(400, result.status_code)
        self.assertEqual('Player does not own enough cities', result.get_data().decode('utf-8'))
