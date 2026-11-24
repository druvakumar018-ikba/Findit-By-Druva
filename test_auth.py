import os
import unittest
from unittest.mock import patch

import config as config_module
from app import create_app
from config import Config
from models import Category, Item, User, db


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = 'test-secret-key-at-least-thirty-two-bytes'
    JWT_SECRET_KEY = 'test-jwt-secret-key-at-least-thirty-two-bytes'
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

    @classmethod
    def get_database_uri(cls):
        return cls.SQLALCHEMY_DATABASE_URI


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def register(self, email='person@example.test', phone=''):
        return self.client.post('/api/auth/register', json={
            'name': 'FindIt User',
            'email': email,
            'phone': phone,
            'password': 'SafePassword123!'
        })

    def report_payload(self, contact_phone='+919876543210'):
        with self.app.app_context():
            category_id = Category.query.first().id
        return {
            'report_type': 'lost',
            'item_name': 'Blue water bottle',
            'category_id': category_id,
            'description': 'Blue bottle with a silver sticker on the side.',
            'location': 'Central library, second floor',
            'event_date': '2026-11-22',
            'contact_phone': contact_phone
        }

    def test_registration_hashes_password_and_returns_a_session(self):
        response = self.register(email=' New.User@Example.Test ')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json['success'])
        self.assertNotIn('password_hash', response.json['user'])
        self.assertEqual(response.json['user']['email'], 'new.user@example.test')

        with self.app.app_context():
            user = User.query.filter_by(email='new.user@example.test').one()
            self.assertNotEqual(user.password_hash, 'SafePassword123!')
            self.assertTrue(user.check_password('SafePassword123!'))

        headers = {'Authorization': f"Bearer {response.json['token']}"}
        self.assertEqual(self.client.get('/api/auth/me', headers=headers).status_code, 200)

    def test_any_valid_email_can_register_and_login(self):
        self.assertEqual(self.register(email='student@gmail.com').status_code, 201)
        response = self.client.post('/api/auth/login', json={
            'email': ' STUDENT@gmail.com ',
            'password': 'SafePassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

    def test_wrong_password_and_unregistered_email_are_rejected(self):
        self.assertEqual(self.register().status_code, 201)
        wrong_password = self.client.post('/api/auth/login', json={
            'email': 'person@example.test',
            'password': 'WrongPassword123!'
        })
        unknown_email = self.client.post('/api/auth/login', json={
            'email': 'unknown@example.test',
            'password': 'SafePassword123!'
        })
        self.assertEqual(wrong_password.status_code, 401)
        self.assertEqual(unknown_email.status_code, 401)
        self.assertEqual(wrong_password.json['message'], unknown_email.json['message'])

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.assertEqual(self.register(email='Person@example.test').status_code, 201)
        response = self.register(email='person@EXAMPLE.test')
        self.assertEqual(response.status_code, 409)

    def test_password_validation_is_enforced(self):
        response = self.client.post('/api/auth/register', json={
            'name': 'Short Password',
            'email': 'short@example.test',
            'password': 'short'
        })
        self.assertEqual(response.status_code, 400)

    def test_reporting_needs_contact_phone_but_not_otp(self):
        registration = self.register()
        headers = {'Authorization': f"Bearer {registration.json['token']}"}
        missing_phone = self.client.post(
            '/api/items',
            json=self.report_payload(contact_phone=''),
            headers=headers
        )
        self.assertEqual(missing_phone.status_code, 400)

        response = self.client.post(
            '/api/items',
            json=self.report_payload(),
            headers=headers
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['item']['contact_phone'], '+919876543210')
        self.assertEqual(response.json['item']['contact_email'], 'person@example.test')

        with self.app.app_context():
            self.assertEqual(Item.query.filter_by(user_id=registration.json['user']['id']).count(), 1)

    def test_reporting_still_requires_an_authenticated_account(self):
        response = self.client.post('/api/items', json=self.report_payload())
        self.assertEqual(response.status_code, 401)

    def test_logout_revokes_the_session(self):
        registration = self.register()
        headers = {'Authorization': f"Bearer {registration.json['token']}"}
        self.assertEqual(self.client.post('/api/auth/logout', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me', headers=headers).status_code, 401)

    def test_serverless_requires_a_persistent_database_url(self):
        with patch.object(config_module, 'IS_SERVERLESS', True), patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'persistent database'):
                Config.get_database_uri()


if __name__ == '__main__':
    unittest.main()
