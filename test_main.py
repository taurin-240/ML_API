import unittest
from main import app  # Импортируйте ваше Flask приложение

class TestAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_predict(self):
        response = self.app.post('/predict', json={'data': [1, 2, 3]})
        self.assertEqual(response.status_code, 200)
        self.assertIn('prediction', response.json)