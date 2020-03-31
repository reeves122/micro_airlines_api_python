import logging
import os
import unittest
import time

import boto3
import moto

from definitions.cities import cities

logging.basicConfig(level=logging.INFO)


class TestCities(unittest.TestCase):

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

    def _create_table(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.dynamodb.create_table(
            TableName='players',
            AttributeDefinitions=[
                {
                    'AttributeName': 'player_id',
                    'AttributeType': 'S'
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'player_id',
                    'KeyType': 'HASH'
                }
            ]
        )

    def _populate_table(self, balance=100000):
        table = self.dynamodb.Table(name='players')
        table.put_item(Item={
            'player_id': self.player_name,
            'balance': balance,
            'cities': {
                '123': {
                    'name': 'foo'
                }
            }
        })

    @moto.mock_dynamodb2
    def test_cities_get(self):
        self._create_table()
        self._populate_table()
        result = self.http_client.get('/v1/cities')
        self.assertEqual({
            '123': {
                'name': 'foo'
            }
        }, result.get_json())
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_get_player_not_exist(self):
        self._create_table()
        result = self.http_client.get('/v1/cities')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post(self):
        self._create_table()
        self._populate_table(balance=11000)

        # Make the request and assert the response
        result = self.http_client.post('/v1/cities?city=a0')
        self.assertEqual({
            'balance': 1000
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        table = self.dynamodb.Table(name='players')
        result = table.get_item(Key={'player_id': self.player_name}).get('Item')
        self.assertEqual(cities['a0'].serialize(), result['cities']['a0'])

    @moto.mock_dynamodb2
    def test_cities_post_missing_arg(self):
        self._create_table()
        result = self.http_client.post('/v1/cities')
        self.assertEqual('Query param "city" is required', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_city_not_exist(self):
        self._create_table()
        result = self.http_client.post('/v1/cities?city=foobar123')
        self.assertEqual('Requested city does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_player_not_exist(self):
        self._create_table()
        result = self.http_client.post('/v1/cities?city=a0')
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(409, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_city_cant_afford(self):
        self._create_table()
        self._populate_table(balance=1000)

        # Make the request and assert the response
        result = self.http_client.post('/v1/cities?city=a0')
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(409, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post_city_already_owned(self):
        self._create_table()
        self._populate_table(balance=90000)

        # Purchase the city first
        result = self.http_client.post('/v1/cities?city=a0')
        self.assertEqual(201, result.status_code)

        # Try to purchase the same city again
        result = self.http_client.post('/v1/cities?city=a0')
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(409, result.status_code)

    @moto.mock_dynamodb2
    def test_get_player_city_jobs(self):
        self._create_table()
        table = self.dynamodb.Table(name='players')
        table.put_item(Item={
            'player_id': self.player_name,
            'cities': {
                '0': {
                    'name': 'foo'
                },
                '1': {
                    'name': 'foo'
                },
                '2': {
                    'name': 'foo'
                }
            }
        })

        result = self.http_client.get('/v1/cities/0/jobs')
        self.assertEqual(200, result.status_code)
        self.assertEqual(30, len(result.get_json()['new_jobs']))
        jobs_expire = result.get_json()['jobs_expire']
        self.assertLess(time.time(), jobs_expire)

        # Make the same call again to see if cached jobs are used
        result = self.http_client.get('/v1/cities/0/jobs')
        self.assertEqual(jobs_expire, result.get_json()['jobs_expire'])
