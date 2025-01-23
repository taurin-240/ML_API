import unittest
import json

from fastapi.testclient import TestClient
from main import app 

class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_predict(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)