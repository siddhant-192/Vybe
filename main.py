import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy import select
from sqlalchemy import Column, Date, Float, DateTime
from sqlalchemy.sql.expression import func

from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import joinedload

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from datetime import datetime, timedelta, date

import random

import os
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for
from flask import flash, jsonify
from flask_sqlalchemy import SQLAlchemy

from flask_login import current_user

from api import api_bp

from models import db, User, Artist, Album, Song, Playlist, Playlist_Song, User_Rating, Genre, Following

current_dir= os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(current_dir,"vybe_database.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
app.register_blueprint(api_bp, url_prefix='')

db.init_app(app)
app.app_context().push()

@app.route("/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        type = request.form.get("type")

        if type=="user":
            user = User.query.filter_by(Username=username, Pass=password).first()

            if user:
                # Redirect to the user's home page with success parameter
                return redirect(url_for('user_home', user_name=username, success=True))
            else:
                # Prompt incorrect username or password
                return render_template('login.html', error="Incorrect username or password")
        elif type=="admin":
            user = User.query.filter_by(Username=username, Pass=password, UserType="Admin").first()

            if user:
                # Redirect to the user's home page with success parameter
                return redirect(url_for('admin_dashboard', user_name=username, success=True))
            else:
                # Prompt incorrect username or password
                return render_template('login.html', error="Incorrect username or password")

    # Get the success parameter from the URL
    signup_success = request.args.get('success')

    # Handle GET request (display the login form)
    return render_template('login.html', error=None, signup_success=signup_success)


@app.route("/<user_name>/home", methods=["GET", "POST"])
def user_home(user_name):
    user = User.query.filter_by(Username=user_name).first()

    if user:
        user_id = user.UserID

        followed_artist_ids = Following.query.filter_by(UserID=user_id).with_entities(Following.ArtistID).all()
        followed_artist_ids = [row[0] for row in followed_artist_ids]

        followed_artists = Artist.query.filter(Artist.ArtistID.in_(followed_artist_ids)).all()
        random.shuffle(followed_artists)
        random_artists = followed_artists[:8]

        if not random_artists:
            additional_artists = Artist.query.order_by(func.random()).limit(8).all()
            random_artists.extend(additional_artists)

        return render_template('user_home.html', random_artists=random_artists, user=user)
    else:
        return render_template('error.html', user_name=user_name)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error_message = None

    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        location = request.form.get("location")

        # Check for null values
        if not all([name, username, password, email, location]):
            error_message = "All fields must be filled"
        else:
            try:
                # Check if the email already exists
                existing_email = User.query.filter_by(Email=email).one_or_none()
                if existing_email:
                    raise IntegrityError("Email already exists", None, None)

                # Try to add the new user to the database
                new_user = User(Name=name, Username=username, Pass=password, Email=email, Loc=location, UserType='General')
                db.session.add(new_user)
                db.session.commit()

                # Redirect to the login page after successful signup with a success parameter
                return redirect(url_for('login', success=True))
            except IntegrityError as e:
                # Handle the case where a unique constraint is violated
                db.session.rollback()
                error_message = "Username or email already exists"
            except NoResultFound:
                # Handle the case where no result is found (email not found)
                error_message = "Email not found in the database"

    # Handle GET request (display the signup form)
    return render_template("signup.html", error=error_message)

@app.route("/<user_name>/profile", methods=["GET", "POST"], endpoint="user_profile")
def user_profile(user_name):
    user = User.query.filter_by(Username=user_name).first()

    if user:
        user_id = user.UserID

        # Retrieve the list of artists that the user follows
        following_artists = Following.query.filter_by(UserID=user_id).all()
        playlists = Playlist.query.filter_by(UserID=user_id).all()

        # Extract artist details for each followed artist
        followed_artists_details = []
        for following_artist in following_artists:
            artist_id = following_artist.ArtistID
            artist = Artist.query.get(artist_id)
            if artist:
                followed_artists_details.append({
                    'id': artist.ArtistID,
                    'name': artist.ArtistName,
                    'description': artist.Description,
                    # Add more details as needed
                })

        # Extract playlist details along with their songs
        playlists_details = []
        for playlist in playlists:
            playlist_details = {
                'id': playlist.PlaylistID,
                'name': playlist.Name,
                'description': playlist.Description,
                # Add more details as needed
            }

            # Extract songs for the playlist using a join
            playlist_details['songs'] = db.session.query(Song.SongID, Song.Name).join(Playlist_Song).filter(Playlist_Song.PlaylistID == playlist.PlaylistID).all()

            playlists_details.append(playlist_details)

        if user.UserType == 'General':
            return render_template('profile.html', user=user, user_name=user_name, followed_artists=followed_artists_details, count_followed_artist=len(followed_artists_details), playlists=playlists_details)
        elif user.UserType == 'Creator':
            # Fetch songs associated with the creator
            curr_artist = Artist.query.filter_by(Username=user.Username).first()
            creator_songs = Song.query.filter_by(ArtistID=curr_artist.ArtistID).all()

            # Fetch albums associated with the creator
            creator_albums = Album.query.options(joinedload(Album.songs)).filter_by(ArtistID=curr_artist.ArtistID).all()

            creator_songs_details = [{
                'id': song.SongID,
                'name': song.Name,
                # Add more song details as needed
            } for song in creator_songs]

            creator_albums_details = [{
                'id': album.AlbumID,
                'genre':album.Genre,
                'name': album.Name,
                'songs': [{
                    'id': song.SongID,
                    'name': song.Name,
                    # Add more song details as needed
                } for song in album.songs]
                # Add more album details as needed
            } for album in creator_albums]

            return render_template('profile.html', user=user, user_name=user_name, followed_artists=followed_artists_details, count_followed_artist=len(followed_artists_details), playlists=playlists_details, creator_songs=creator_songs_details, creator_albums=creator_albums_details)
    else:
        return render_template('error.html', user_name=user_name)


@app.route("/unfollow_artist/<int:user_id>/<int:artist_id>", methods=["POST"])
def unfollow_artist(user_id,artist_id):
    # Get the current user
    user = User.query.filter_by(UserID=user_id).first()

    if user:
        # Remove the relationship in the Following table
        following_entry = Following.query.filter_by(UserID=user_id, ArtistID=artist_id).first()
        if following_entry:
            db.session.delete(following_entry)
            db.session.commit()

    # Redirect back to the user home page
    return redirect(url_for('user_home', user_name=user.Username))

@app.route("/follow_artist/<int:user_id>/<int:artist_id>", methods=["POST"])
def follow_artist(user_id, artist_id):
    # Get the current user
    user = User.query.filter_by(UserID=user_id).first()

    if user:
        # Check if the user is not already following the artist
        if not Following.query.filter_by(UserID=user_id, ArtistID=artist_id).first():
            # Create a new entry in the Following table
            new_following = Following(UserID=user_id, ArtistID=artist_id)
            db.session.add(new_following)
            db.session.commit()

    # Redirect back to the user home page
    return redirect(url_for('user_home', user_name=user.Username))

@app.route("/update_profile/<user_id>", methods=["POST"])
def update_profile(user_id):
    # Get the current user
    user = User.query.filter_by(UserID=user_id).first()

    profile_edit_success = None  # Initialize to None

    if user:
        # Update user profile information based on the form data
        user.Name = request.form.get("newInputName")
        temp_pass = request.form.get("newInputPassword")  # Note: This should be the password field, not email
        user.UserType = request.form.get("userTypeCreator")
        if temp_pass:
            user.Pass = temp_pass
        user.Loc = request.form.get("newInputLocation")
        
        if user.UserType=='Creator':
            artist = Artist.query.filter_by(ArtistName=user.Name).first()
            if artist:
                artist.ArtistName=user.Name
                artist.Loc=user.Loc
                artist.Pass=user.Pass
                artist.Username=user.Username
            else:
                artist_new=Artist(ArtistName=user.Name, Pass=user.Pass, Loc=user.Loc, Email=user.Email, Username=user.Username)
                db.session.add(artist_new)
        elif user.UserType=='General':
            artist = Artist.query.filter_by(ArtistName=user.Name).first()
            if artist:
                db.session.delete(artist)


        # Commit the changes to the database
        db.session.commit()

        # Set the success message
        profile_edit_success = 'Profile updated successfully!'

    # Render the user profile page with the success message
    return redirect(url_for('user_profile', user_name=user.Username, profile_edit_success='Profile updated successfully!'))

'''@app.route("/create_playlist_form/<int:user_id>", methods=["GET"])
def create_playlist_form(user_id):
    if user_id:
        user_id = int(user_id)
    else:
        return redirect(url_for('error_page'))
    
    user = User.query.get(user_id)
    songs = Song.query.join(Artist).all()
    return render_template('create_playlist.html', user=user, songs=songs)

@app.route("/create_playlist/<int:user_id>", methods=["POST"])
def create_playlist(user_id):
    user = User.query.get(user_id)

    if user:
        playlist_name = request.form.get("playlistName")
        song_ids = request.form.getlist("songs")

        try:
            # Create a new playlist
            new_playlist = Playlist(Name=playlist_name, UserID=user_id)
            db.session.add(new_playlist)
            db.session.commit()

            # Add songs to the playlist
            for position, song_id in enumerate(song_ids):
                new_playlist_song = Playlist_Song(PlaylistID=new_playlist.PlaylistID, SongID=song_id, Position=position)
                db.session.add(new_playlist_song)
            
            db.session.commit()

            flash("Playlist created successfully!", "success")
            return redirect(url_for('user_profile', user_name=user.Username))
        except IntegrityError:
            db.session.rollback()
            flash("Error creating playlist. Please try again.", "danger")
            return redirect(url_for('create_playlist_form', user_id=user_id))
    else:
        return render_template('user_not_found.html', user_name=user.Username)
'''

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

#Manage User
@app.route('/add_users', methods=['POST'])
def add_users():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        location = request.form.get('location')

        # Add user to the database (you need to hash the password in a real application)
        new_user = User(Username=username, Name=name, Pass=password, Email=email, Loc=location, UserType="General")
        db.session.add(new_user)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/edit_users', methods=['POST'])
def edit_users():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        location = request.form.get('location')

        user = User.query.filter_by(Username=username, UserType="General").first()

        # Add user to the database (you need to hash the password in a real application)
        user.Name = name
        user.Pass = password
        user.Loc = location
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/delete_users', methods=['POST'])
def delete_users():
    if request.method == 'POST':
        username = request.form.get('username')

        user = User.query.filter_by(Username=username).first()

        if user:
            # Delete the user
            db.session.delete(user)
            db.session.commit()

            # Redirect to a page (e.g., user management page)
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template("error.html")    
    else:
        # Handle the case where the user is not found
        return render_template("error.html")
    
#Manage Creator
@app.route('/add_creators', methods=['POST'])
def add_creators():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        location = request.form.get('location')
        description = request.form.get('description')

        # Add user to the database (you need to hash the password in a real application)
        new_user = User(Username=username, Name=name, Pass=password, Email=email, Loc=location, UserType="Creator")
        new_artist = Artist(Username=username, ArtistName=name, Description=description, Pass=password, Email=email, Loc=location)
        db.session.add(new_user)
        db.session.add(new_artist)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/edit_creators', methods=['POST'])
def edit_creators():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        location = request.form.get('location')
        description = request.form.get('description')

        user = User.query.filter_by(Username=username, UserType="Creator").first()
        artist = Artist.query.filter_by(Username=username, ArtistName=user.Name).first()

        # Add user to the database (you need to hash the password in a real application)
        user.Name = name
        user.Pass = password
        user.Loc = location
        artist.ArtistName=name
        artist.Description=description
        artist.Username=username
        artist.Pass = password
        artist.Loc = location
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/delete_creators', methods=['POST'])
def delete_creators():
    if request.method == 'POST':
        username = request.form.get('username')

        user = User.query.filter_by(Username=username, UserType="Creator").first()
        name = user.Name
        artist = Artist.query.filter_by(Username=username, ArtistName=name).first()

        if user:
            # Delete the user
            db.session.delete(user)
            db.session.delete(artist)
            db.session.commit()

            # Redirect to a page (e.g., user management page)
            return redirect(url_for('admin_dashboard'))
    else:
        # Handle the case where the user is not found
        return render_template("error.html", username=user.Username)
    
#Manage Album
@app.route('/add_album', methods=['POST'])
def add_album():
    if request.method == 'POST':
        name=request.form.get('name')
        genre=request.form.get('genre')
        rdate=request.form.get('releasedate')
        datetime_object = datetime.strptime(rdate, '%Y-%m-%d').date()
        artist_name=request.form.get('artist')

        # Add user to the database (you need to hash the password in a real application)
        artist = Artist.query.filter_by(ArtistName=artist_name).first()
        artist_id = artist.ArtistID
        new_album = Album(Name=name, Genre=genre, ReleaseDate=datetime_object, ArtistID=artist_id)
        db.session.add(new_album)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

'''
@app.route('/get_songs_from_artist', methods=['POST'])
def get_songs_from_artist():
    if request.method == 'POST':
        artist_name = request.form.get('artist')

        # Query artist based on the provided artist name
        artist = Artist.query.filter_by(ArtistName=artist_name).first()

        if artist:
            # If the artist is found, get the songs belonging to that artist
            artist_songs = Song.query.filter_by(ArtistID=artist.ArtistID).all()

            # Create an array to store song details
            song_details_array = []

            # Iterate through each song and extract relevant details
            for song in artist_songs:
                song_details = {
                    'SongID': song.SongID,
                    'Name': song.Name,
                    'Lyrics': song.Lyrics,
                    'Duration': song.Duration,
                    'ReleaseDate': song.ReleaseDate,
                    'AlbumID': song.AlbumID,
                    'Rating': song.Rating,
                    'ArtistID': song.ArtistID
                    # Add other relevant details as needed
                }
                song_details_array.append(song_details)

            return render_template('song_details.html', songs=song_details_array)

        else:
            # Handle the case where the artist is not found
            return render_template('artist_not_found.html')

    return render_template('invalid_request.html')
'''

@app.route('/edit_album', methods=['POST'])
def edit_album():
    if request.method == 'POST':
        name=request.form.get('name')
        newname=request.form.get('newname')
        genre=request.form.get('genre')
        rdate=request.form.get('releasedate')
        datetime_object = datetime.strptime(rdate, '%Y-%m-%d').date()

        # Add user to the database (you need to hash the password in a real application)
        album = Album.query.filter_by(Name=name).first()
        
        album.Name = newname
        album.Genre = genre
        album.ReleaseDate = datetime_object

        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/delete_album', methods=['POST'])
def delete_album():
    if request.method == 'POST':
        name = request.form.get('name')

        album = Album.query.filter_by(Name=name).first()

        if album:
            # Delete the user
            db.session.delete(album)
            db.session.commit()

            # Redirect to a page (e.g., user management page)
            return redirect(url_for('admin_dashboard'))
    else:
        # Handle the case where the user is not found
        return render_template("error.html", name=album.Name)
    
#Manage Song
@app.route('/add_song', methods=['POST'])
def add_song():
    if request.method == 'POST':
        name=request.form.get('name')
        lyrics=request.form.get('lyrics')
        rdate=request.form.get('releasedate')
        datetime_object = datetime.strptime(rdate, '%Y-%m-%d').date()
        artist_name=request.form.get('artist')
        album_name=request.form.get('album')
        duration=request.form.get('duration')

        album = Album.query.filter_by(Name=album_name).first()
        album_id = album.AlbumID

        artist = Artist.query.filter_by(ArtistName=artist_name).first()
        artist_id = artist.ArtistID
        
        # Add user to the database (you need to hash the password in a real application)
        new_song = Song(Name=name, Lyrics=lyrics, Duration=duration, ReleaseDate=datetime_object,AlbumID=album_id, ArtistID=artist_id)
        db.session.add(new_song)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/edit_song', methods=['POST'])
def edit_song():
    if request.method == 'POST':
        name=request.form.get('name')
        newname=request.form.get('newname')
        lyrics=request.form.get('lyrics')
        rdate=request.form.get('releasedate')
        datetime_object = datetime.strptime(rdate, '%Y-%m-%d').date()
        artist_name=request.form.get('artist')
        album_name=request.form.get('album')
        dur=request.form.get('duration')
        duration=int(dur)

        song = Song.query.filter_by(Name=name).first()

        album = Album.query.filter_by(Name=album_name).first()
        album_id = album.AlbumID

        artist = Artist.query.filter_by(ArtistName=artist_name).first()
        artist_id = artist.ArtistID
        
        # Updating database
        song.Name=newname
        song.Lyrics=lyrics
        song.Duration=duration
        song.ReleaseDate=datetime_object
        song.AlbumID=album_id
        song.ArtistID=artist_id

        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/delete_song', methods=['POST'])
def delete_song():
    if request.method == 'POST':
        name = request.form.get('name')

        song = Song.query.filter_by(Name=name).first()

        if song:
            # Delete the user
            db.session.delete(song)
            db.session.commit()

            # Redirect to a page (e.g., user management page)
            return redirect(url_for('admin_dashboard'))
    else:
        # Handle the case where the user is not found
        return render_template("not_found.html", name=song.Name)

#calculates the target date, and returns the user count
def get_user_count_for_past_days(days):
    # Calculate the date N days ago
    target_date = datetime.utcnow() - timedelta(days=days)

    # Query the number of users created on the specific date and before
    user_count = (
        User.query.filter(func.date(User.CreationDate) <= target_date.date()).count()
    )

    return user_count
    
@app.route('/get_user_count')
def get_user_count():
    user_counts = {}

    last_month_user = get_user_count_for_past_days(0) - get_user_count_for_past_days(30)

    #get data for alst 5 days the concurrent user count
    for days_ago in range(0, 5):
        user_count = get_user_count_for_past_days(days_ago)
        user_counts[str(days_ago)] = user_count
    return jsonify({'userCounts': user_counts, 'last_month_user':last_month_user})

#calculates the target date, and returns the creator count
def get_creator_count_for_past_days(days):
    # Calculate the date N days ago
    target_date = datetime.utcnow() - timedelta(days=days)

    # Query the number of users created on the specific date and before
    creator_count = (
        Artist.query.filter(func.date(Artist.CreationDate) <= target_date.date()).count()
    )

    return creator_count

@app.route('/get_creator_count')
def get_creator_count():
    creator_counts = {}

    last_month_creator = get_creator_count_for_past_days(0) - get_creator_count_for_past_days(30)

    #get data for alst 5 days the concurrent user count
    for days_ago in range(0, 5):
        creator_count = get_creator_count_for_past_days(days_ago)
        creator_counts[str(days_ago)] = creator_count
    return jsonify({'creatorCounts': creator_counts, 'last_month_creator':last_month_creator})

#calculates the target date, and returns the song count
def get_song_count_for_past_days(days):
    # Calculate the date N days ago
    target_date = datetime.utcnow() - timedelta(days=days)

    # Query the number of users created on the specific date and before
    song_count = (
        Song.query.filter(func.date(Song.CreationDate) <= target_date.date()).count()
    )

    return song_count

@app.route('/get_song_count')
def get_song_count():
    song_counts = {}

    last_month_song = get_song_count_for_past_days(0) - get_song_count_for_past_days(30)

    #get data for alst 5 days the concurrent user count
    for days_ago in range(0, 5):
        song_count = get_song_count_for_past_days(days_ago)
        song_counts[str(days_ago)] = song_count
    return jsonify({'songCounts': song_counts, 'last_month_song':last_month_song})

#calculates the target date, and returns the album count
def get_album_count_for_past_days(days):
    # Calculate the date N days ago
    target_date = datetime.utcnow() - timedelta(days=days)

    # Query the number of users created on the specific date and before
    album_count = (
        Album.query.filter(func.date(Album.CreationDate) <= target_date.date()).count()
    )

    return album_count

@app.route('/get_album_count')
def get_album_count():
    album_counts = {}

    last_month_album = get_album_count_for_past_days(0) - get_album_count_for_past_days(30)

    #get data for alst 5 days the concurrent user count
    for days_ago in range(0, 5):
        album_count = get_album_count_for_past_days(days_ago)
        album_counts[str(days_ago)] = album_count
    return jsonify({'albumCounts': album_counts, 'last_month_album':last_month_album})

@app.route('/search')
def search():
    user_name = request.args.get('user_name', '')
    return render_template('search.html', user_name=user_name)

@app.route('/search_bar/<phrase>')
def search_bar(phrase):
    
    # Perform a search across multiple tables
    song_results = Song.query.filter(Song.Name.ilike(f"%{phrase}%")).all()
    user_results = User.query.filter(User.Name.ilike(f"%{phrase}%")).all()
    artist_results = Artist.query.filter(Artist.ArtistName.ilike(f"%{phrase}%")).all()
    album_results = Album.query.filter(Album.Name.ilike(f"%{phrase}%")).all()

    # Convert results to JSON format
    results_json = {
        "songs": [{"name": song.Name} for song in song_results],
        "users": [{"name": user.Name} for user in user_results],
        "artists": [{"name": artist.ArtistName} for artist in artist_results],
        "albums": [{"name": album.Name, "id": album.AlbumID} for album in album_results]
    }

    return jsonify(results_json)

@app.route('/library')
def library():
    user_name = request.args.get('user_name', '')
    # Query all songs, albums, and artists from the database
    all_songs = Song.query.all()
    all_albums = Album.query.all()
    all_artists = Artist.query.all()

    # Render the "library.html" page and pass the queried data to the template
    return render_template('library.html', songs=all_songs, albums=all_albums, artists=all_artists, user_name=user_name)

# Rename the function to avoid conflicts
def is_following_artist(user_id, artist_id):
    # Check if there is an entry in the Following table for the given user and artist
    following_entry = Following.query.filter_by(UserID=user_id, ArtistID=artist_id).first()
    
    return following_entry is not None

@app.route('/is_following/<int:user_id>/<int:artist_id>')
def is_following(user_id, artist_id):
    # Check if there is an entry in the Following table for the given user and artist
    following_entry = Following.query.filter_by(UserID=user_id, ArtistID=artist_id).first()

    # Return the result in JSON format
    return jsonify({"is_following": following_entry is not None})

@app.route('/artist/<artist_name>')
def artist_page(artist_name):
    username = request.args.get('user_name', '')
    user = User.query.filter_by(Username=username).first()

    if user:
        artist = Artist.query.filter_by(ArtistName=artist_name).first()
        songs = Song.query.filter_by(ArtistID=artist.ArtistID).all()
        albums = Album.query.filter_by(ArtistID=artist.ArtistID).all()

        if artist:
            is_following_artist_bool = is_following_artist(user.UserID, artist.ArtistID)
            return render_template('artist_page.html', artist=artist, user_name=username, user=user, songs=songs, albums=albums)
        else:
            # Handle the case where the artist does not exist
            return render_template('error.html', error_message="Artist not found", username=username)
    else:
        # Handle the case where the user does not exist
        return render_template('error.html', error_message="User not found", username=username)
    
@app.route('/album/<album_id>')
def album_page(album_id):
    user_name = request.args.get('user_name', '')
    album = Album.query.filter_by(AlbumID=album_id).first()

    if album:
        artist = None
        if album.ArtistID is not None:
            artist = Artist.query.filter_by(ArtistID=album.ArtistID).first()

        songs = Song.query.filter_by(AlbumID=album_id).all()

        return render_template('album_page.html', album=album, songs=songs, artist=artist, user_name=user_name)
    else:
        return render_template('error.html', error_message="Album not found", username=user_name)

@app.route('/follow/<artist_id>/<user_id>', methods=['GET', 'POST'])
def follow(artist_id, user_id):
    user = User.query.filter_by(UserID=user_id).first()
    artist = Artist.query.filter_by(ArtistID=artist_id).first()

    if user and artist:
        # Check if the user is already following the artist
        if not is_following_artist(user.UserID, artist.ArtistID):
            new_follow = Following(UserID=user.UserID, ArtistID=artist.ArtistID)
            db.session.add(new_follow)
            db.session.commit()

            # Return a success response (you can customize this based on your needs)
            return jsonify({"message": "Followed successfully"})
        else:
            # Return a response indicating that the user is already following the artist
            return jsonify({"message": "User is already following the artist"})
    else:
        # Return an error response (you can customize this based on your needs)
        return jsonify({"error": "User or artist not found"})

@app.route('/unfollow/<artist_id>/<user_id>', methods=['GET', 'POST'])
def unfollow(artist_id, user_id):
    if request.method == 'POST':
        user = User.query.filter_by(UserID=user_id).first()
        artist = Artist.query.filter_by(ArtistID=artist_id).first()

        if user and artist:
            follow_obj = Following.query.filter_by(UserID=user.UserID, ArtistID=artist.ArtistID).first()
            db.session.delete(follow_obj)
            db.session.commit()

            # Return a success response (you can customize this based on your needs)
            return jsonify({"message": "Unfollowed successfully"})
        else:
            # Return an error response (you can customize this based on your needs)
            return jsonify({"error": "User or artist not found"})
    else:
        # Handle the case where the method is not allowed (e.g., return a 405 response)
        return jsonify({"error": "Method not allowed"}), 405


@app.route('/song_page/<song_name>')
def song_page(song_name):
    username = request.args.get('user_name', '')
    user = User.query.filter_by(Username=username).first()
    avgRate=0

    if user:
        song = Song.query.filter_by(Name=song_name).first()
        artist = Artist.query.filter_by(ArtistID=song.ArtistID).first()
        album = Album.query.filter_by(AlbumID=song.AlbumID).first()
        user_playlists = Playlist.query.filter_by(UserID=user.UserID).all()

        if song:
            average_rating = db.session.query(func.avg(User_Rating.Rating)).filter(User_Rating.SongID == song.SongID).scalar()
            if average_rating is not None:
                avgRate=average_rating
            else:
                avgRate="No Ratings Yet"

        if song and artist:
            # Check if there's a rating for the user and song
            user_rating = User_Rating.query.filter_by(UserID=user.UserID, SongID=song.SongID).first()

            if user_rating:
                rating = user_rating.Rating
                comments = user_rating.Comments
            else:
                rating = None
                comments = None

            return render_template('song_page.html', song=song, user_name=username, user=user, artist=artist, album=album, user_playlists=user_playlists, rating=rating, comments=comments, averageRating = avgRate)
        else:
            # Handle the case where the artist does not exist
            return render_template('error.html', error_message="Song not found", username=username)
    else:
        # Handle the case where the user does not exist
        return render_template('error.html', error_message="User not found", username=username)


@app.route('/create_playlist/<int:user_id>', methods=['POST'])
def create_playlist(user_id):
    user = User.query.get(user_id)

    if user:
        playlist_name = request.form.get('playlistName')
        playlist_description = request.form.get('playlistDescription')

        if playlist_name:
            new_playlist = Playlist(Name=playlist_name, Description=playlist_description, UserID=user.UserID)
            db.session.add(new_playlist)
            db.session.commit()

            # Optionally, you can redirect to the user's profile page
            return redirect(url_for('user_profile', user_name=user.Username))
        else:
            # Handle the case where the playlist name is not provided
            return render_template('error.html', error_message="Playlist name is required", username=user.Username)

    else:
        # Handle the case where the user is not found
        return render_template('error.html', error_message="User not found", username=user.Username)
    
@app.route('/add_to_playlist/<int:playlist_id>/<int:song_id>', methods=['GET'])
def add_to_playlist(playlist_id, song_id):
    playlist = Playlist.query.filter_by(PlaylistID=playlist_id).first()
    song = Song.query.filter_by(SongID=song_id).first()

    username = request.args.get('user_name', '')
    user = User.query.filter_by(Username=username).first()

    if playlist and song and user:
        new_playlist_song = Playlist_Song(PlaylistID=playlist.PlaylistID, SongID=song.SongID)
        db.session.add(new_playlist_song)
        db.session.commit()

        # Return a success response (you can customize this based on your needs)
        return jsonify({"message": "Song added to playlist successfully"})
    else:
        # Return an error response (you can customize this based on your needs)
        return jsonify({"error": "Invalid playlist, song, or user"})

@app.route('/remove_from_playlist/<int:playlist_id>/<int:song_id>', methods=['POST'])
def remove_from_playlist(playlist_id, song_id):
    playlist = Playlist.query.get(playlist_id)
    song = Song.query.get(song_id)

    if playlist and song:
        playlist_song = Playlist_Song.query.filter_by(PlaylistID=playlist_id, SongID=song_id).first()

        if playlist_song:
            db.session.delete(playlist_song)
            db.session.commit()

            return jsonify({"message": "Song removed from playlist successfully"})
        else:
            return jsonify({"error": "Song not found in the playlist"})
    else:
        return jsonify({"error": "Invalid playlist or song"})
    
@app.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
def delete_playlist(playlist_id):
    playlist = Playlist.query.filter_by(PlaylistID=playlist_id).first()

    if playlist:
        playlist_songs = Playlist_Song.query.filter_by(PlaylistID=playlist_id).all()

        for playlist_song in playlist_songs:
            db.session.delete(playlist_song)

        db.session.delete(playlist)
        db.session.commit()

        return jsonify({"message": "Playlist deleted successfully"})
    else:
        return jsonify({"error": "Playlist not found"})

@app.route('/add_song_by_artist', methods=['POST'])
def add_song_by_artist():
    if request.method == 'POST':
        song_data = request.get_json()

        name = song_data.get('name')
        lyrics = song_data.get('lyrics')
        duration = song_data.get('duration')
        release_date_str = song_data.get('releaseDate')
        album_name = song_data.get('albumName')

        username = request.args.get('user_name', '')
        user = User.query.filter_by(Username=username).first()
        artist = Artist.query.filter_by(Username=username).first()

        if user and artist:
            artist_id = artist.ArtistID

            # Convert the string representation of the date to a Python date object
            release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()

            # Retrieve album details from the database
            album = Album.query.filter_by(Name=album_name).first()

            if album:
                album_id = album.AlbumID

                # Add song to the database
                new_song = Song(
                    Name=name,
                    Lyrics=lyrics,
                    Duration=duration,
                    ReleaseDate=release_date,
                    AlbumID=album_id,
                    ArtistID=artist_id
                )
                db.session.add(new_song)
                db.session.commit()

                # Return a JSON response indicating success
                return jsonify({"message": "Song added successfully"})
            else:
                # Add song to the database
                new_song = Song(
                    Name=name,
                    Lyrics=lyrics,
                    Duration=duration,
                    ReleaseDate=release_date,
                    ArtistID=artist_id
                )
                db.session.add(new_song)
                db.session.commit()

                # Return a JSON response indicating success
                return jsonify({"message": "Song added successfully"})

    # Return a JSON response indicating an error
    return jsonify({"error": "Invalid request"})


# Add Album by Artist
@app.route('/add_album_by_artist', methods=['POST'])
def add_album_by_artist():
    if request.method == 'POST':
        album_data = request.get_json()

        album_name = album_data.get('name')
        genre = album_data.get('genre')
        release_date_str = album_data.get('releaseDate')

        username = request.args.get('user_name', '')
        artist = Artist.query.filter_by(Username=username).first()

        if artist:
            artist_id = artist.ArtistID

            # Convert the string representation of the date to a Python date object
            release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()

            # Add album to the database
            new_album = Album(
                Name=album_name,
                Genre=genre,
                ReleaseDate=release_date,
                ArtistID=artist_id
            )
            db.session.add(new_album)
            db.session.commit()

            # Return a JSON response indicating success
            return jsonify({"message": "Album added successfully"})

    # Return a JSON response indicating an error
    return jsonify({"error": "Invalid request"})

@app.route('/delete_album_by_artist', methods=['POST'])
def delete_album_by_artist():
    if request.method == 'POST':
        # Get album ID from the JSON request
        data = request.get_json()
        album_id = data.get('albumId')

        # Perform the album deletion logic 
        album = Album.query.filter_by(AlbumID=album_id).first()
        db.session.delete(album)
        db.session.commit()

        # Return a JSON response indicating success
        return jsonify({"message": "Album deleted successfully"})

    # Return a JSON response indicating an error
    return jsonify({"error": "Invalid request"})

@app.route('/delete_song_by_artist', methods=['POST'])
def delete_song_by_artist():
    if request.method == 'POST':
        # Get album ID from the JSON request
        data = request.get_json()
        song_id = data.get('songId')

        # Perform the album deletion logic 
        song = Song.query.filter_by(SongID=song_id).first()
        db.session.delete(song)
        db.session.commit()

        # Return a JSON response indicating success
        return jsonify({"message": "Song deleted successfully"})

    # Return a JSON response indicating an error
    return jsonify({"error": "Invalid request"})

@app.route('/error')
def error():
    username = request.args.get('username', '')
    return render_template('error.html', user_name=username)

@app.route('/add_rating', methods=['POST'])
def add_rating():
    try:
        # Get data from the request
        rating = request.json['rating']
        comments = request.json['comment']  # <-- Use 'comment' instead of 'comments'
        user_name = request.json['username']
        song_name = request.json['song_name']

        # Retrieve user and song from the database
        user = User.query.filter_by(Username=user_name).first()
        song = Song.query.filter_by(Name=song_name).first()

        if user and song:
            # Check if the user already rated the song
            user_rating = User_Rating.query.filter_by(UserID=user.UserID, SongID=song.SongID).first()

            if user_rating:
                # Update the existing rating
                user_rating.Rating = rating
                user_rating.Comments = comments
            else:
                # Create a new User_Rating instance
                new_rating = User_Rating(
                    Rating=rating,
                    Comments=comments,
                    UserID=user.UserID,
                    SongID=song.SongID,
                    CreationDate=datetime.utcnow()
                )

                # Add the new rating to the database
                db.session.add(new_rating)

            # Commit changes to the database
            db.session.commit()

            return jsonify({"message": "Rating added successfully"}), 200
        else:
            return jsonify({"error": "User or song not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')



if __name__ == "__main__":
    #Run flask app
    app.run(
        host='0.0.0.0',
        debug=True,
        port=8080
    )