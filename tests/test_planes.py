import logging
import os
import unittest.mock
import time

import moto

from definitions.planes import planes
from tests import shared_test_utils
from utils import utils

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

    @moto.mock_dynamodb2
    def test_planes_get(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100000)
        utils.add_plane_to_player(player_id=self.player_name, plane_id='a1', current_city_id='a1')
        result = self.http_client.get('/v1/planes')

        _, first_plane = result.get_json()['planes'].popitem()

        self.assertEqual(planes['a1'].serialize(), first_plane)
        self.assertEqual(200, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_get_not_exist(self):
        shared_test_utils.create_table()
        result = self.http_client.get('/v1/planes')
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(404, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=300)

        result = self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.assertEqual({
            'balance': 100
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        _, result = utils.get_player_attributes(self.player_name, attributes_to_get=['planes'])
        _, first_plane = result['planes'].popitem()
        self.assertEqual(planes['a1'].serialize(), first_plane)

    @moto.mock_dynamodb2
    def test_planes_post_multiple(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=600)

        result = self.http_client.post('/v1/planes', json={'plane': 'a0', 'city': 'a1'})
        self.assertEqual({
            'balance': 400
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        result = self.http_client.post('/v1/planes', json={'plane': 'a0', 'city': 'a1'})
        self.assertEqual({
            'balance': 200
        }, result.get_json())
        self.assertEqual(201, result.status_code)

        # Query the table to validate the result
        _, result = utils.get_player_attributes(self.player_name, attributes_to_get=['planes'])
        self.assertEqual(2, len(result['planes'].keys()))

    @moto.mock_dynamodb2
    def test_planes_post_missing_arg(self):
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/planes')
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_plane_not_exist(self):
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/planes', json={'plane': 'foobar123'})
        self.assertEqual('Plane does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_player_not_exist(self):
        shared_test_utils.create_table()
        result = self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_planes_post_plane_cant_afford(self):
        shared_test_utils.create_table()
        utils.create_player(player_id=self.player_name, balance=100)

        # Make the request and assert the response
        result = self.http_client.post('/v1/planes', json={'plane': 'a0', 'city': 'a1'})
        self.assertEqual('Purchase failed', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_plane_depart_no_body(self):
        result = self.http_client.put('/v1/planes/abcxyz/depart')
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_plane_depart_empty_body(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        plane_id, _ = self.http_client.get('/v1/planes').get_json().get('planes').popitem()

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={})
        self.assertEqual('No changes specified', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_plane_depart_bad_player(self):
        shared_test_utils.create_table()
        result = self.http_client.put(f'/v1/planes/12345/depart', json={'jobs': 'foo'})
        self.assertEqual('Player does not exist', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_plane_depart_invalid_plane(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        result = self.http_client.put(f'/v1/planes/12345/depart', json={'jobs': 'foo'})
        self.assertEqual('Invalid plane_id', result.get_data().decode('utf-8'))
        self.assertEqual(400, result.status_code)

    @moto.mock_dynamodb2
    def test_plane_depart_jobs_success(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a2'})
        self.http_client.post('/v1/cities', json={'city': 'a3'})
        jobs = self.http_client.get('/v1/cities/a1/jobs').get_json().get('jobs')
        plane_id, _ = self.http_client.get('/v1/planes').get_json().get('planes').popitem()

        # Pick some jobs of compatible type
        job_ids = [key for key, values in jobs.items()
                   if values.get('job_type') == 'C'][:4]

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={
            'loaded_jobs': job_ids
        })
        self.assertEqual(200, result.status_code)

        # Check that our plane is loaded now
        _, plane = self.http_client.get('/v1/planes').get_json().get('planes').popitem()
        self.assertEqual(4, len(plane.get('loaded_jobs')))

        # Check that jobs were removed from city
        jobs = self.http_client.get('/v1/cities/a1/jobs').get_json().get('jobs')
        self.assertEqual(26, len(jobs))

    @moto.mock_dynamodb2
    def test_plane_depart_jobs_too_many(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a2'})
        self.http_client.post('/v1/cities', json={'city': 'a3'})
        jobs = self.http_client.get('/v1/cities/a1/jobs').get_json().get('jobs')
        plane_id, _ = self.http_client.get('/v1/planes').get_json().get('planes').popitem()

        # Pick some jobs of compatible type
        job_ids = [key for key, values in jobs.items()
                   if values.get('job_type') == 'C'][:5]

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={
            'loaded_jobs': job_ids
        })
        self.assertEqual(400, result.status_code)
        self.assertEqual('Not enough capacity', result.get_data().decode('utf-8'))

    @moto.mock_dynamodb2
    def test_plane_depart_jobs_too_many_already_loaded(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a2'})
        self.http_client.post('/v1/cities', json={'city': 'a3'})
        jobs = self.http_client.get('/v1/cities/a1/jobs').get_json().get('jobs')
        plane_id, _ = self.http_client.get('/v1/planes').get_json().get('planes').popitem()

        # Pick some jobs of compatible type
        job_ids = [key for key, values in jobs.items()
                   if values.get('job_type') == 'C'][:8]

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={
            'loaded_jobs': job_ids[:4]
        })
        self.assertEqual(200, result.status_code)

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={
            'loaded_jobs': job_ids[5:]
        })
        self.assertEqual(400, result.status_code)
        self.assertEqual('Not enough capacity', result.get_data().decode('utf-8'))

    @moto.mock_dynamodb2
    def test_plane_depart_jobs_expired(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a2'})
        self.http_client.post('/v1/cities', json={'city': 'a3'})
        jobs = self.http_client.get('/v1/cities/a1/jobs').get_json().get('jobs')
        plane_id, _ = self.http_client.get('/v1/planes').get_json().get('planes').popitem()

        # Update city to fake the jobs expiring
        utils.table.update_item(
            Key={'player_id': self.player_name},
            UpdateExpression="SET cities.a1.jobs_expire = :jobs_expire",
            ExpressionAttributeValues={
                ':jobs_expire': int(time.time() - 60)
            })

        # Pick some jobs of compatible type
        job_ids = [key for key, values in jobs.items()
                   if values.get('job_type') == 'C'][:4]

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={
            'loaded_jobs': job_ids
        })
        self.assertEqual(400, result.status_code)
        self.assertEqual('Jobs have expired', result.get_data().decode('utf-8'))

    @moto.mock_dynamodb2
    def test_plane_depart_jobs_wrong_job_id(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a2'})
        self.http_client.post('/v1/cities', json={'city': 'a3'})
        self.http_client.get('/v1/cities/a1/jobs').get_json().get('new_jobs')
        plane_id, _ = self.http_client.get('/v1/planes').get_json().get('planes').popitem()

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={
            'loaded_jobs': ['foo']
        })
        self.assertEqual(400, result.status_code)
        self.assertEqual('One or more job ids is invalid', result.get_data().decode('utf-8'))

    @moto.mock_dynamodb2
    def test_plane_depart_jobs_wrong_job_type(self):
        shared_test_utils.create_table()
        self.http_client.post(f'/v1/player')
        self.http_client.post('/v1/planes', json={'plane': 'a1', 'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a1'})
        self.http_client.post('/v1/cities', json={'city': 'a2'})
        self.http_client.post('/v1/cities', json={'city': 'a3'})
        jobs = self.http_client.get('/v1/cities/a1/jobs').get_json().get('jobs')
        plane_id, _ = self.http_client.get('/v1/planes').get_json().get('planes').popitem()

        # Pick some jobs of not compatible type
        job_ids = [key for key, values in jobs.items()
                   if values.get('job_type') == 'P'][:5]

        result = self.http_client.put(f'/v1/planes/{plane_id}/depart', json={
            'loaded_jobs': job_ids
        })
        self.assertEqual(400, result.status_code)
        self.assertEqual('Not enough capacity', result.get_data().decode('utf-8'))
