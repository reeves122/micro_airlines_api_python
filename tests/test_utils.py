import logging
import os
import unittest

from flask import request
from flask import Flask
import moto

from definitions.cities import cities
from tests import shared_test_utils

logging.basicConfig(level=logging.INFO)


class TestUtils(unittest.TestCase):

    def setUp(self):
        """
        Initialize test http client and set up the requestContext
        :return:
        """
        # These are needed to avoid a credential error when testing
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

        from utils import utils
        self.utils = utils

        self.player_name = 'test_player_1'
        self.http_client = Flask(__name__)

    def test_get_username_cognito(self):
        """
        Test getting username from cognito
        """
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
            self.assertEqual(self.player_name, self.utils.get_username())

    def test_get_username_apikey(self):
        """
        Test getting username from apiKey
        """
        with self.http_client.test_request_context():
            request.environ['awsgi.event'] = {
                'requestContext': {
                    'identity': {
                        'apiKey': 'abc123'
                    }
                }
            }
            self.assertEqual('abc123', self.utils.get_username())

    def test_generate_random_jobs(self):
        """
        Test generating random jobs
        """
        player_cities = {
            'c1001': cities['c1001'],
            'c1002': cities['c1002'],
            'c1003': cities['c1003'],
            'c1004': cities['c1004']
        }

        result = self.utils.generate_random_jobs(player_cities, '0')

        p_jobs = [i for i in result.values() if i['job_type'] == 'P']
        c_jobs = [i for i in result.values() if i['job_type'] == 'C']

        self.assertTrue(5 < len(p_jobs) > 5)
        self.assertTrue(5 < len(c_jobs) > 5)

    def test_generate_random_string(self):
        """
        Test generating a random string
        """
        result = self.utils.generate_random_string()
        self.assertEqual(20, len(result))

    @moto.mock_dynamodb2
    def test_create_player(self):
        """
        Test creating a player
        """
        shared_test_utils.create_table()
        created, message = self.utils.create_player(player_id='foo', balance=10000)
        self.assertTrue(created)
        self.assertEqual('Player "foo" created with balance: 10000', message)

    @moto.mock_dynamodb2
    def test_create_player_already_exists(self):
        """
        Test creating a player that already exists
        """
        shared_test_utils.create_table()
        created, message = self.utils.create_player(player_id='foo', balance=10000)
        self.assertTrue(created)
        self.assertEqual('Player "foo" created with balance: 10000', message)

        created, message = self.utils.create_player(player_id='foo', balance=10000)
        self.assertFalse(created)
        self.assertEqual('Player "foo" already exists', message)

    @moto.mock_dynamodb2
    def test_get_player_attributes(self):
        """
        Test getting player attributes
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=10000)

        success, result = self.utils.get_player_attributes(player_id='foo',
                                                           attributes_to_get=['player_id'])
        self.assertTrue(success)
        self.assertEqual('foo', result['player_id'])

    @moto.mock_dynamodb2
    def test_get_player_attributes_not_exist(self):
        """
        Test getting player attributes when player does not exist
        """
        shared_test_utils.create_table()
        success, result = self.utils.get_player_attributes(player_id='foo',
                                                           attributes_to_get=['player_id'])
        self.assertFalse(success)
        self.assertEqual('Player does not exist', result)

    @moto.mock_dynamodb2
    def test_add_city_to_player(self):
        """
        Test adding a city to a player
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=10000)
        success, result = self.utils.add_city_to_player(player_id='foo', city_id='c1001')
        self.assertTrue(success)
        self.assertEqual(7222, result.get('balance'))

    @moto.mock_dynamodb2
    def test_add_city_to_player_not_exist(self):
        """
        Test adding a city to a player when city does not exist
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=10000)
        success, result = self.utils.add_city_to_player(player_id='foo', city_id='foo123')
        self.assertFalse(success)
        self.assertEqual('City does not exist', result)

    @moto.mock_dynamodb2
    def test_add_city_to_player_cant_afford(self):
        """
        Test adding a city to a player when player cannot afford city
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=1000)
        success, result = self.utils.add_city_to_player(player_id='foo', city_id='c1001')
        self.assertFalse(success)
        self.assertEqual('Purchase failed', result)

    @moto.mock_dynamodb2
    def test_add_city_to_player_already_owned(self):
        """
        Test adding a city to a player when player already owns city
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=20000)
        success, result = self.utils.add_city_to_player(player_id='foo', city_id='c1001')
        self.assertTrue(success)
        self.assertEqual(17222, result.get('balance'))

        success, result = self.utils.add_city_to_player(player_id='foo', city_id='c1001')
        self.assertFalse(success)
        self.assertEqual('Purchase failed', result)

    @moto.mock_dynamodb2
    def test_add_plane_to_player(self):
        """
        Test adding a plane to a player
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=200)
        success, result = self.utils.add_plane_to_player(player_id='foo', plane_id='a1',
                                                         current_city_id='c1001')
        self.assertTrue(success)
        self.assertEqual(0, result.get('balance'))

    @moto.mock_dynamodb2
    def test_add_plane_to_player_not_exist(self):
        """
        Test adding a plane to a player that does not exist
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=10000)
        success, result = self.utils.add_plane_to_player(player_id='foo', plane_id='foo123',
                                                         current_city_id='c1001')
        self.assertFalse(success)
        self.assertEqual('Plane does not exist', result)

    @moto.mock_dynamodb2
    def test_add_plane_to_player_cant_afford(self):
        """
        Test adding a plane to a player when player cannot afford
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=199)
        success, result = self.utils.add_plane_to_player(player_id='foo', plane_id='a1',
                                                         current_city_id='c1001')
        self.assertFalse(success)
        self.assertEqual('Purchase failed', result)

    @moto.mock_dynamodb2
    def test_add_jobs_to_plane(self):
        """
        Test adding a jobs to a plane
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=100000)
        self.utils.add_plane_to_player(player_id='foo', plane_id='a1', current_city_id='c1001')
        self.utils.add_city_to_player(player_id='foo', city_id='c1001')
        self.utils.add_city_to_player(player_id='foo', city_id='c1002')
        self.utils.add_city_to_player(player_id='foo', city_id='c1003')

        # Get the new cities and plane added to the player
        _, result = self.utils.get_player_attributes(player_id='foo',
                                                     attributes_to_get=['cities', 'planes'])

        plane_1_id, _ = result.get('planes').popitem()
        player_cities = result.get('cities')

        # Generate some random jobs
        jobs = self.utils.generate_random_jobs(player_cities=player_cities, current_city_id='c1001')

        # Add the jobs to the plane
        success, _ = self.utils.add_jobs_to_plane(
            player_id='foo', plane_id=plane_1_id, list_of_jobs=jobs)
        self.assertTrue(success)

        # Check the jobs added to the plane
        _, result = self.utils.get_player_attributes(player_id='foo',
                                                     attributes_to_get=['planes'])
        self.assertEqual(30, len(result['planes'][plane_1_id]['loaded_jobs']))

    @moto.mock_dynamodb2
    def test_remove_jobs_from_city(self):
        """
        Test removing jobs from a city
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=100000)
        self.utils.add_plane_to_player(player_id='foo', plane_id='a1', current_city_id='c1001')
        self.utils.add_city_to_player(player_id='foo', city_id='c1001')
        self.utils.add_city_to_player(player_id='foo', city_id='c1002')
        self.utils.add_city_to_player(player_id='foo', city_id='c1003')

        # Get the new cities added to the player
        _, result = self.utils.get_player_attributes(player_id='foo', attributes_to_get=['cities'])
        player_cities = result.get('cities')

        jobs, _ = self.utils.update_city_with_new_jobs(player_id='foo', city_id='c1001',
                                                       player_cities=player_cities)
        jobs_ids_to_remove = [
            jobs.popitem()[0],
            jobs.popitem()[0],
            jobs.popitem()[0]
        ]
        self.utils.remove_jobs_from_city(player_id='foo', city_id='c1001',
                                         list_of_jobs=jobs_ids_to_remove)

        _, result = self.utils.get_player_attributes(player_id='foo', attributes_to_get=['cities'])
        city_jobs = result.get('cities').get('c1001').get('jobs')
        print(len(city_jobs))

    @moto.mock_dynamodb2
    def test_handle_plane_landed(self):
        """
        Test unloading a plane once it has landed
        """
        shared_test_utils.create_table()
        self.utils.create_player(player_id='foo', balance=100000)
        self.utils.add_plane_to_player(player_id='foo', plane_id='a1', current_city_id='c1001')
        self.utils.add_city_to_player(player_id='foo', city_id='c1001')
        self.utils.add_city_to_player(player_id='foo', city_id='c1002')
        self.utils.add_city_to_player(player_id='foo', city_id='c1003')

        # Get the new cities and plane added to the player
        _, result = self.utils.get_player_attributes(player_id='foo',
                                                     attributes_to_get=['cities', 'planes'])

        plane_1_id, plane_1_values = result.get('planes').popitem()
        player_cities = result.get('cities')

        # Generate some random jobs
        jobs = self.utils.generate_random_jobs(player_cities=player_cities,
                                               current_city_id='c1001', count=8)

        # Add the jobs to the plane
        success, _ = self.utils.add_jobs_to_plane(
            player_id='foo', plane_id=plane_1_id, list_of_jobs=jobs)
        self.assertTrue(success)

        self.utils.depart_plane(player_id='foo', plane_id=plane_1_id,
                                destination_city_id='c1002', eta=1)

        # Get the updated plane
        _, result = self.utils.get_player_attributes(player_id='foo', attributes_to_get=['planes'])
        _, plane_1_values = result.get('planes').popitem()

        # Check the result of handling the plane landing
        success, result = self.utils.handle_plane_landed(player_id='foo', plane_id=plane_1_id,
                                                         plane=plane_1_values)
        self.assertTrue(success)
        self.assertLess(69800, int(result.get('balance')))

        # Check the updated plane for the correct values after landing the plane
        _, result = self.utils.get_player_attributes(player_id='foo', attributes_to_get=['planes'])
        _, plane_1_values = result.get('planes').popitem()
        self.assertEqual(0, plane_1_values['eta'])
        self.assertEqual('none', plane_1_values['destination_city_id'])
        self.assertEqual('c1002', plane_1_values['current_city_id'])
        self.assertGreater(8, len(plane_1_values['loaded_jobs']))
