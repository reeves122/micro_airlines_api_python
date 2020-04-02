import logging
import os
import unittest

from flask import request
from flask import Flask
import moto

from definitions.cities import cities
from utils import utils
from tests import shared_test_utils

logging.basicConfig(level=logging.INFO)


class TestUtils(unittest.TestCase):

    def setUp(self):
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
        self.player_name = 'test_player_1'
        self.http_client = Flask(__name__)

    def test_get_username_cognito(self):
        with self.http_client.test_request_context():
            request.environ['awsgi.event'] = {
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': self.player_name
                        }
                    }
                }
            }
            self.assertEqual(self.player_name, utils.get_username())

    def test_get_username_apikey(self):
        with self.http_client.test_request_context():
            request.environ['awsgi.event'] = {
                'requestContext': {
                    'identity': {
                        'apiKey': 'abc123'
                    }
                }
            }
            self.assertEqual('abc123', utils.get_username())

    def test_generate_random_jobs(self):
        player_cities = {
            '0': cities['a0'],
            '1': cities['a1'],
            '2': cities['a2'],
            '3': cities['a3']
        }

        result = utils.generate_random_jobs(player_cities, '0')

        p_jobs = [i for i in result.values() if i['job_type'] == 'P']
        c_jobs = [i for i in result.values() if i['job_type'] == 'C']

        self.assertTrue(5 < len(p_jobs) > 5)
        self.assertTrue(5 < len(c_jobs) > 5)

    def test_generate_random_string(self):
        result = utils.generate_random_string()
        self.assertEqual(20, len(result))

    @moto.mock_dynamodb2
    def test_create_player(self):
        shared_test_utils.create_table()
        created, message = utils.create_player(player_id='foo', balance=10000)
        self.assertTrue(created)
        self.assertEqual('Player "foo" created with balance: 10000', message)

    @moto.mock_dynamodb2
    def test_create_player_already_exists(self):
        shared_test_utils.create_table()
        created, message = utils.create_player(player_id='foo', balance=10000)
        self.assertTrue(created)
        self.assertEqual('Player "foo" created with balance: 10000', message)

        created, message = utils.create_player(player_id='foo', balance=10000)
        self.assertFalse(created)
        self.assertEqual('Player "foo" already exists', message)

    @moto.mock_dynamodb2
    def test_get_player_attributes(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=10000)

        success, result = utils.get_player_attributes(player_id='foo',
                                                      attributes_to_get=['player_id'])
        self.assertTrue(success)
        self.assertEqual('foo', result['player_id'])

    @moto.mock_dynamodb2
    def test_get_player_attributes_not_exist(self):
        shared_test_utils.create_table()
        success, result = utils.get_player_attributes(player_id='foo',
                                                      attributes_to_get=['player_id'])
        self.assertFalse(success)
        self.assertEqual('Player does not exist', result)

    @moto.mock_dynamodb2
    def test_add_city_to_player(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=10000)
        success, result = utils.add_city_to_player(player_id='foo', city_id='a1')
        self.assertTrue(success)
        self.assertEqual(0, result.get('balance'))

    @moto.mock_dynamodb2
    def test_add_city_to_player_not_exist(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=10000)
        success, result = utils.add_city_to_player(player_id='foo', city_id='foo123')
        self.assertFalse(success)
        self.assertEqual('City does not exist', result)

    @moto.mock_dynamodb2
    def test_add_city_to_player_cant_afford(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=9000)
        success, result = utils.add_city_to_player(player_id='foo', city_id='a1')
        self.assertFalse(success)
        self.assertEqual('Purchase failed', result)

    @moto.mock_dynamodb2
    def test_add_city_to_player_already_owned(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=20000)
        success, result = utils.add_city_to_player(player_id='foo', city_id='a1')
        self.assertTrue(success)
        self.assertEqual(10000, result.get('balance'))

        success, result = utils.add_city_to_player(player_id='foo', city_id='a1')
        self.assertFalse(success)
        self.assertEqual('Purchase failed', result)

    @moto.mock_dynamodb2
    def test_add_plane_to_player(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=200)
        success, result = utils.add_plane_to_player(player_id='foo', plane_id='a1',
                                                    current_city_id='a1')
        self.assertTrue(success)
        self.assertEqual(0, result.get('balance'))

    @moto.mock_dynamodb2
    def test_add_plane_to_player_not_exist(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=10000)
        success, result = utils.add_plane_to_player(player_id='foo', plane_id='foo123',
                                                    current_city_id='a1')
        self.assertFalse(success)
        self.assertEqual('Plane does not exist', result)

    @moto.mock_dynamodb2
    def test_add_plane_to_player_cant_afford(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=199)
        success, result = utils.add_plane_to_player(player_id='foo', plane_id='a1',
                                                    current_city_id='a1')
        self.assertFalse(success)
        self.assertEqual('Purchase failed', result)

    @moto.mock_dynamodb2
    def test_add_jobs_to_plane(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=100000)
        utils.add_plane_to_player(player_id='foo', plane_id='a1', current_city_id='a1')
        utils.add_city_to_player(player_id='foo', city_id='a1')
        utils.add_city_to_player(player_id='foo', city_id='a2')
        utils.add_city_to_player(player_id='foo', city_id='a3')

        # Get the new cities and plane added to the player
        _, result = utils.get_player_attributes(player_id='foo',
                                                attributes_to_get=['cities', 'planes'])

        plane_1_id, _ = result.get('planes').popitem()
        player_cities = result.get('cities')

        # Generate some random jobs
        jobs = utils.generate_random_jobs(player_cities=player_cities, current_city_id='a1')

        # Add the jobs to the plane
        success, _ = utils.add_jobs_to_plane_and_set_destination(
            player_id='foo', plane_id=plane_1_id, list_of_jobs=jobs, destination_city_id='a2')
        self.assertTrue(success)

        # Check the jobs added to the plane
        _, result = utils.get_player_attributes(player_id='foo',
                                                attributes_to_get=['planes'])

        self.assertEqual(30, len(result['planes'][plane_1_id]['loaded_jobs']))
        self.assertLess(1585848803, int(result['planes'][plane_1_id]['eta']))

    @moto.mock_dynamodb2
    def test_remove_jobs_from_city(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=100000)
        utils.add_plane_to_player(player_id='foo', plane_id='a1', current_city_id='a1')
        utils.add_city_to_player(player_id='foo', city_id='a1')
        utils.add_city_to_player(player_id='foo', city_id='a2')
        utils.add_city_to_player(player_id='foo', city_id='a3')

        # Get the new cities added to the player
        _, result = utils.get_player_attributes(player_id='foo', attributes_to_get=['cities'])
        player_cities = result.get('cities')

        jobs, _ = utils.update_city_with_new_jobs(player_id='foo', city_id='a1',
                                                  player_cities=player_cities)
        jobs_ids_to_remove = [
            jobs.popitem()[0],
            jobs.popitem()[0],
            jobs.popitem()[0]
        ]
        utils.remove_jobs_from_city(player_id='foo', city_id='a1', list_of_jobs=jobs_ids_to_remove)

        _, result = utils.get_player_attributes(player_id='foo', attributes_to_get=['cities'])
        city_jobs = result.get('cities').get('a1').get('jobs')
        print(len(city_jobs))

    @moto.mock_dynamodb2
    def test_handle_plane_landed(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=100000)
        utils.add_plane_to_player(player_id='foo', plane_id='a1', current_city_id='a1')
        utils.add_city_to_player(player_id='foo', city_id='a1')
        utils.add_city_to_player(player_id='foo', city_id='a2')
        utils.add_city_to_player(player_id='foo', city_id='a3')

        # Get the new cities and plane added to the player
        _, result = utils.get_player_attributes(player_id='foo',
                                                attributes_to_get=['cities', 'planes'])

        plane_1_id, plane_1_values = result.get('planes').popitem()
        player_cities = result.get('cities')

        # Generate some random jobs
        jobs = utils.generate_random_jobs(player_cities=player_cities,
                                          current_city_id='a1', count=8)

        # Add the jobs to the plane
        success, _ = utils.add_jobs_to_plane_and_set_destination(
            player_id='foo', plane_id=plane_1_id, list_of_jobs=jobs,
            destination_city_id='a2', eta=1)
        self.assertTrue(success)

        _, result = utils.get_player_attributes(player_id='foo', attributes_to_get=['planes'])
        _, plane_1_values = result.get('planes').popitem()
        print(plane_1_values)

        success, result = utils.handle_plane_landed(player_id='foo', plane_id=plane_1_id,
                                                    plane=plane_1_values)
        self.assertTrue(success)
        self.assertLess(69800, int(result.get('balance')))


