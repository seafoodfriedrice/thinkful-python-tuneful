import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

import sys; print sys.modules.keys()
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def testGetEmptySong(self):
        """ Get song list from empty database """
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/json")]
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        data = json.loads(response.data)
        self.assertEqual(data, [])

    def testSongPost(self):
        """ Post a new song """
        data = {
            "file": {
                "name": "new_song.mp3"
            }
        }
        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs")

    def testSongPut(self):
        """ Post a new song """
        data = {
            "file": {
                "name": "new_song.mp3"
            }
        }
        # Create song using POST which will create File.id = 1
        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs")
        post_data = json.loads(response.data)
        self.assertEqual(post_data["file"]["name"], "new_song.mp3")
        # Change file name and use PUT to update to File.id = 1
        data["file"]["name"] = "updated_song.mp3"
        response = self.client.put("/api/songs/1",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        updated_data = json.loads(response.data)
        self.assertEqual(updated_data["file"]["name"], "updated_song.mp3")
