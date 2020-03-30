import logging
import os
import unittest

import boto3
import moto

from definitions.planes import planes


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
            'planes': {}
        })

    @moto.mock_dynamodb2
    def test_planes_get(self):
        self._create_table()
        table = self.dynamodb.Table(name='players')
        table.put_item(Item={
            'player_id': self.player_name,
            'planes': {
                '123': planes['0'].serialize()
            }
        })
        result = self.http_client.get('/v1/planes')
        self.assertEqual({
            '123': planes['0'].serialize()
        }, result.get_json())
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_get_not_exist(self):
        self._create_table()
        result = self.http_client.get('/v1/planes')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post(self):
        self._create_table()
        self._populate_table(balance=300)

        result = self.http_client.post('/v1/planes?plane=0')
        self.assertEqual({
            'balance': 100
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        table = self.dynamodb.Table(name='players')
        result = table.get_item(Key={'player_id': self.player_name}).get('Item')
        for plane_id, plane in result['planes'].items():
            self.assertEqual(36, len(plane_id))
            self.assertEqual(planes['0'].serialize(), plane)

    @moto.mock_dynamodb2
    def test_planes_post_multiple(self):
        self._create_table()
        self._populate_table(balance=600)

        result = self.http_client.post('/v1/planes?plane=0')
        self.assertEqual({
            'balance': 400
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        result = self.http_client.post('/v1/planes?plane=0')
        self.assertEqual({
            'balance': 200
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        table = self.dynamodb.Table(name='players')
        result = table.get_item(Key={'player_id': self.player_name}).get('Item')
        self.assertEqual(2, len(result['planes']))

    @moto.mock_dynamodb2
    def test_planes_post_missing_arg(self):
        self._create_table()
        result = self.http_client.post('/v1/planes')
        self.assertEqual('Query param "plane" is required', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_plane_not_exist(self):
        self._create_table()
        result = self.http_client.post('/v1/planes?plane=foobar123')
        self.assertEqual('Requested plane does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_player_not_exist(self):
        self._create_table()
        result = self.http_client.post('/v1/planes?plane=0')
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(409, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_plane_cant_afford(self):
        self._create_table()
        self._populate_table(balance=100)

        # Make the request and assert the response
        result = self.http_client.post('/v1/planes?plane=0')
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(409, result.status_code)
