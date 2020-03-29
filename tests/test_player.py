import logging
import unittest
from unittest import mock

import boto3
import moto

from micro_airlines_api import app


logging.basicConfig(level=logging.INFO)


class TestPlayer(unittest.TestCase):

    def setUp(self):
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
            'player_id': self.player_name
        })

    @moto.mock_dynamodb2
    def test_player_get(self):
        self._create_table()
        self._populate_table()
        result = self.http_client.get('/v1/player')
        self.assertEqual({
            'player_id': self.player_name
        }, result.get_json())
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_player_get_not_exist(self):
        self._create_table()
        result = self.http_client.get('/v1/player')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_player_post(self):
        self._create_table()
        result = self.http_client.post('/v1/player')
        self.assertEqual('Player created', result.get_data().decode('utf-8'))
        self.assertEqual(201, result.status_code)

    @moto.mock_dynamodb2
    def test_player_post_already_exist(self):
        self._create_table()
        self._populate_table()
        result = self.http_client.post('/v1/player')
        self.assertEqual('Player already exists', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)