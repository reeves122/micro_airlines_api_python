import logging
import os
import unittest
from unittest import mock

import boto3
import moto

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

    def _populate_table(self):
        table = self.dynamodb.Table(name='players')
        table.put_item(Item={
            'player_id': self.player_name,
            'balance': 600,
            'planes': {
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
    def test_cities_get_not_exist(self):
        self._create_table()
        result = self.http_client.get('/v1/cities')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_cities_post(self):
        self._create_table()
        self._populate_table()
        result = self.http_client.post('/v1/cities?city=0')
        self.assertEqual('City added for player', result.get_data().decode('utf-8'))
        self.assertEqual(201, result.status_code)
        table = self.dynamodb.Table(name='players')
        result = table.get_item(Key={'player_id': self.player_name}).get('Item')
        print(result)

    # @moto.mock_dynamodb2
    # def test_planes_post_missing_arg(self):
    #     self._create_table()
    #     result = self.http_client.post('/v1/planes')
    #     self.assertEqual('Query param "plane" is required', result.get_data().decode('utf-8'))
    #     self.assertEqual(400, result.status_code)
    #
    # @moto.mock_dynamodb2
    # def test_planes_post_plane_not_exist(self):
    #     self._create_table()
    #     result = self.http_client.post('/v1/planes?plane=foobar123')
    #     self.assertEqual('Requested plane doesnt exist', result.get_data().decode('utf-8'))
    #     self.assertEqual(400, result.status_code)
    #
    # @moto.mock_dynamodb2
    # def test_planes_post_player_not_exist(self):
    #     self._create_table()
    #     result = self.http_client.post('/v1/planes?plane=foobar123')
    #     self.assertEqual('Player doesnt exist', result.get_data().decode('utf-8'))
    #     self.assertEqual(400, result.status_code)
    #
    # @moto.mock_dynamodb2
    # def test_planes_post_player_cant_afford(self):
    #     self._create_table()
    #     result = self.http_client.post('/v1/planes?plane=foobar123')
    #     self.assertEqual('Player cant afford', result.get_data().decode('utf-8'))
    #     self.assertEqual(400, result.status_code)
    #
    #
    #
    #
