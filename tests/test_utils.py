import logging
import unittest

from definitions.cities import cities
from utils import utils

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
