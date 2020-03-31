import logging
import unittest

import moto

from definitions.cities import cities
from utils import utils
from tests import shared_test_utils

logging.basicConfig(level=logging.INFO)


class TestUtils(unittest.TestCase):

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
        self.assertEqual('Player "foo" created', message)

    @moto.mock_dynamodb2
    def test_create_player_already_exists(self):
        shared_test_utils.create_table()
        created, message = utils.create_player(player_id='foo', balance=10000)
        self.assertTrue(created)
        self.assertEqual('Player "foo" created', message)

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
        success, result = utils.add_plane_to_player(player_id='foo', plane_id='a1')
        self.assertTrue(success)
        self.assertEqual(0, result.get('balance'))

    @moto.mock_dynamodb2
    def test_add_plane_to_player_not_exist(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=10000)
        success, result = utils.add_plane_to_player(player_id='foo', plane_id='foo123')
        self.assertFalse(success)
        self.assertEqual('Plane does not exist', result)

    @moto.mock_dynamodb2
    def test_add_plane_to_player_cant_afford(self):
        shared_test_utils.create_table()
        utils.create_player(player_id='foo', balance=199)
        success, result = utils.add_plane_to_player(player_id='foo', plane_id='a1')
        self.assertFalse(success)
        self.assertEqual('Purchase failed', result)
