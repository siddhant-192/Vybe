from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from models import db, User, Artist, Album, Song, Playlist
from datetime import datetime

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# API Songs
class SongAPI(Resource):
    def get(self, song_id=None):
        if song_id:
            song = Song.query.get(song_id)
            if song:
                return jsonify(song.serialize())
            else:
                return jsonify({"message": "Song not found"}), 404
        else:
            songs = Song.query.all()
            serialized_songs = [song.serialize() for song in songs]
            return jsonify(serialized_songs)

    def post(self):
        data = request.json
        name = data.get('name')
        lyrics = data.get('lyrics')
        release_date_str = data.get('release_date') 

        # Pth Date time
        release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()

        duration = data.get('duration')

        if data:
            new_song = Song(
                Name=name,
                Lyrics=lyrics,
                ReleaseDate=release_date, 
                Duration=duration
            )
            db.session.add(new_song)
            db.session.commit()
            return jsonify({"message": "Song added successfully"}), 201
        else:
            return jsonify({"error": "Invalid artist or album"}), 400

    def put(self, song_id):
        song = Song.query.get(song_id)

        if song:
            data = request.json
            song.Name = data.get('name')
            song.Lyrics = data.get('lyrics')
            song.ReleaseDate = data.get('release_date')
            song.Duration = data.get('duration')

            artist_name = data.get('artist')
            album_name = data.get('album')

            if artist_name:
                artist = Artist.query.filter_by(ArtistName=artist_name).first()
                if artist:
                    song.ArtistID = artist.ArtistID

            if album_name:
                album = Album.query.filter_by(Name=album_name).first()
                if album:
                    song.AlbumID = album.AlbumID

            db.session.commit()
            return jsonify({"message": "Song updated successfully"})
        else:
            return jsonify({"message": "Song not found"}), 404

    def delete(self, song_id):
        song = Song.query.get(song_id)

        if song:
            db.session.delete(song)
            db.session.commit()
            return jsonify({"message": "Song deleted successfully"})
        else:
            return jsonify({"message": "Song not found"}), 404

api.add_resource(SongAPI, '/api/songs', '/api/songs/<int:song_id>')

# API Albums
class AlbumAPI(Resource):
    def get(self, album_id=None):
        if album_id:
            album = Album.query.get(album_id)
            if album:
                return jsonify(album.serialize())
            else:
                return jsonify({"message": "Album not found"}), 404
        else:
            albums = Album.query.all()
            serialized_albums = [album.serialize() for album in albums]
            return jsonify(serialized_albums)

    def post(self):
        data = request.json
        name = data.get('name')
        genre = data.get('genre')
        release_date = data.get('release_date')
        artist_name = data.get('artist')

        artist = Artist.query.filter_by(ArtistName=artist_name).first()

        if artist:
            new_album = Album(
                Name=name,
                Genre=genre,
                ReleaseDate=release_date,
                ArtistID=artist.ArtistID
            )
            db.session.add(new_album)
            db.session.commit()
            return jsonify({"message": "Album added successfully"}), 201
        else:
            return jsonify({"error": "Invalid artist"}), 400

    def put(self, album_id):
        album = Album.query.get(album_id)

        if album:
            data = request.json
            album.Name = data.get('name')
            album.Genre = data.get('genre')
            album.ReleaseDate = data.get('release_date')

            # Update the related Artist (if needed)
            artist_name = data.get('artist')

            if artist_name:
                artist = Artist.query.filter_by(ArtistName=artist_name).first()
                if artist:
                    album.ArtistID = artist.ArtistID

            db.session.commit()
            return jsonify({"message": "Album updated successfully"})
        else:
            return jsonify({"message": "Album not found"}), 404

    def delete(self, album_id):
        album = Album.query.get(album_id)

        if album:
            db.session.delete(album)
            db.session.commit()
            return jsonify({"message": "Album deleted successfully"})
        else:
            return jsonify({"message": "Album not found"}), 404

api.add_resource(AlbumAPI, '/api/albums', '/api/albums/<int:album_id>')

# API Playlist
class PlaylistAPI(Resource):
    def get(self, playlist_id=None):
        if playlist_id:
            playlist = Playlist.query.get(playlist_id)
            if playlist:
                return jsonify(playlist.serialize())
            else:
                return jsonify({"message": "Playlist not found"}), 404
        else:
            playlists = Playlist.query.all()
            serialized_playlists = [playlist.serialize() for playlist in playlists]
            return jsonify(serialized_playlists)

    def post(self):
        data = request.json
        name = data.get('name')
        description = data.get('description')
        user_id = data.get('user_id')

        user = User.query.get(user_id)

        if user:
            new_playlist = Playlist(
                Name=name,
                Description=description,
                UserID=user.UserID
            )
            db.session.add(new_playlist)
            db.session.commit()
            return jsonify({"message": "Playlist added successfully"}), 201
        else:
            return jsonify({"error": "Invalid user"}), 400

    def put(self, playlist_id):
        playlist = Playlist.query.get(playlist_id)

        if playlist:
            data = request.json
            playlist.Name = data.get('name')
            playlist.Description = data.get('description')

            user_id = data.get('user_id')

            if user_id:
                user = User.query.get(user_id)
                if user:
                    playlist.UserID = user.UserID

            db.session.commit()
            return jsonify({"message": "Playlist updated successfully"})
        else:
            return jsonify({"message": "Playlist not found"}), 404

    def delete(self, playlist_id):
        playlist = Playlist.query.get(playlist_id)

        if playlist:
            db.session.delete(playlist)
            db.session.commit()
            return jsonify({"message": "Playlist deleted successfully"})
        else:
            return jsonify({"message": "Playlist not found"}), 404

# Add the PlaylistAPI resource to the API with the specified endpoint
api.add_resource(PlaylistAPI, '/api/playlists', '/api/playlists/<int:playlist_id>')

# Statistics
def get_user_count():
    return User.query.count()

def get_artist_count():
    return Artist.query.count()

def get_song_count():
    return Song.query.count()

def get_album_count():
    return Album.query.count()

class StatisticsAPI(Resource):
    def get(self):
        user_count = get_user_count()
        artist_count = get_artist_count()
        song_count = get_song_count()
        album_count = get_album_count()

        statistics_data = {
            "user_count": user_count,
            "artist_count": artist_count,
            "song_count": song_count,
            "album_count": album_count
        }

        return jsonify(statistics_data)

api.add_resource(StatisticsAPI, '/api/statistics')
