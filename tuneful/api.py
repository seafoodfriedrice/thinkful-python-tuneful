import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

import models
import decorators
from tuneful import app
from database import session
from utils import upload_path


song_schema = {
    "properties": {
        "file": { "type": "object" },
        "id": { "type": "number" },
        "name": { "type": "string" }
    }
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    """ Get list of all songs """
    songs = session.query(models.Song).all()
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def song_post():
    """ Add a new song """
    data = request.json

    try:
        validate(data, song_schema)
    except ValidationError as error:
        data = { "message": error.message }
        return Response(json.dumps(data), 422, mimetype="application/json")

    song = models.Song(file=models.File(name=data["file"]["name"]))
    session.add(song)
    session.commit()

    data = json.dumps(song.as_dictionary())
    headers = { "Location": url_for("songs_get") }
    return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def song_put(id):
    """ Update an existing song """
    data = request.json

    try:
        validate(data, song_schema)
    except ValidationError as error:
        data = { "message": error.message }
        return Response(json.dumps(data), 422, mimetype="application/json")

    song = session.query(models.Song).get(id)
    song.file.name = data["file"]["name"]
    session.add(song)
    session.commit()

    data = json.dumps(song.as_dictionary())
    headers = { "Location": url_for("songs_get") }
    return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["DELETE"])
def song_delete(id):
    """ Delete an existing song """
    song = session.query(models.Song).get(id)
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})

    session.delete(song)
    session.commit()

    message = "File id {} has been deleted.".format(id)
    data = json.dumps({"message": message })
    return Response(data, 200, mimetype="application/json")
