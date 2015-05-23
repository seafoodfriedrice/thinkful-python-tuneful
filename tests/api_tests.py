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
        """ Update an existing song's file name """
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

    def testSongDelete(self):
        """ Delete an existing song's file name """
        data = {
            "file": {
                "name": "new_song.mp3"
            }
        }
        # Add a new song that we will use to delete
        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs")

        response = self.client.delete("/api/songs/1",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        delete_data = json.loads(response.data)
        self.assertEqual(delete_data["message"],
                         "File id 1 has been deleted.")

    def testGetUploadedFile(self):
        path = upload_path("test.txt")
        with open(path, "w") as f:
            f.write("File contents")

        response = self.client.get("/uploads/test.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, "File contents")

    def testFileUpload(self):
        data = {
            "file": (StringIO("File contents"), "test.txt")
        }

        response = self.client.post("/api/files",
            data=data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        data= json.loads(response.data)
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")

        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            contents = f.read()
        self.assertEqual(contents, "File contents")
