from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Date, Float, ForeignKey

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'
    UserID = Column(Integer, primary_key=True)
    Username = Column(String)
    Name = Column(String)
    Pass = Column(String)
    Email = Column(String)
    UserType = Column(String)
    Loc = Column(String)
    CreationDate = Column(DateTime, default=datetime.utcnow)
    playlists = relationship('Playlist', back_populates='user', cascade='all, delete-orphan')
    ratings = relationship('User_Rating', back_populates='user', cascade='all, delete-orphan')
    followed_artists = relationship('Following', back_populates='user', cascade='all, delete-orphan')

class Artist(db.Model):
    __tablename__ = 'Artist'
    ArtistID = Column(Integer, primary_key=True)
    Username = Column(String)
    ArtistName = Column(String)
    Description = Column(String)
    Pass = Column(String)
    Email = Column(String)
    Loc = Column(String)
    CreationDate = Column(DateTime, default=datetime.utcnow)
    albums = relationship('Album', back_populates='artist', cascade='all, delete-orphan')
    songs = relationship('Song', back_populates='artist', cascade='all, delete-orphan')
    followers = relationship('Following', back_populates='artist', cascade='all, delete-orphan')

class Album(db.Model):
    __tablename__ = 'Album'
    AlbumID = Column(Integer, primary_key=True)
    Name = Column(String)
    Genre = Column(String)
    ReleaseDate = Column(Date)
    ArtistID = Column(Integer, ForeignKey('Artist.ArtistID'))
    CoverImage = Column(String)
    Rating = Column(Float)
    CreationDate = Column(DateTime, default=datetime.utcnow)
    artist = relationship('Artist', back_populates='albums')
    songs = relationship('Song', back_populates='album', cascade='all, delete-orphan')

    def serialize(self):
        return {
            'AlbumID': self.AlbumID,
            'Name': self.Name,
            'Genre': self.Genre,
            'ReleaseDate': str(self.ReleaseDate),
            'ArtistID': self.ArtistID,
            'CoverImage': self.CoverImage,
            'Rating': self.Rating,
            'CreationDate': str(self.CreationDate)
            # Add more fields if needed
        }

class Song(db.Model):
    __tablename__ = 'Song'
    SongID = Column(Integer, primary_key=True)
    Name = Column(String)
    Lyrics = Column(String)
    Duration = Column(Integer)
    ReleaseDate = Column(Date)
    AlbumID = Column(Integer, ForeignKey('Album.AlbumID'))
    Rating = Column(Float)
    ArtistID = Column(Integer, ForeignKey('Artist.ArtistID'))
    CreationDate = Column(DateTime, default=datetime.utcnow)
    album = relationship('Album', back_populates='songs')
    artist = relationship('Artist', back_populates='songs')
    playlists = relationship('Playlist_Song', back_populates='song')
    ratings = relationship('User_Rating', back_populates='song', cascade='all, delete-orphan')

    def serialize(self):
        return {
            'SongID': self.SongID,
            'Name': self.Name,
            'Lyrics': self.Lyrics,
            'Duration': self.Duration,
            'ReleaseDate': str(self.ReleaseDate),
            'AlbumID': self.AlbumID,
            'Rating': self.Rating,
            'ArtistID': self.ArtistID,
            'CreationDate': str(self.CreationDate)
            # Add more fields if needed
        }

class Playlist(db.Model):
    __tablename__ = 'Playlist'
    PlaylistID = Column(Integer, primary_key=True)
    Name = Column(String)
    Description = Column(String)
    UserID = Column(Integer, ForeignKey('User.UserID'))
    CreationDate = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='playlists')
    songs = relationship('Playlist_Song', back_populates='playlist')

    def serialize(self):
        return {
            'PlaylistID': self.PlaylistID,
            'Name': self.Name,
            'Description': self.Description,
            'UserID': self.UserID,
            'CreationDate': str(self.CreationDate)
            # Add more fields if needed
        }

class Playlist_Song(db.Model):
    __tablename__ = 'Playlist_Song'
    PlaylistSongID = Column(Integer, primary_key=True)
    PlaylistID = Column(Integer, ForeignKey('Playlist.PlaylistID'))
    SongID = Column(Integer, ForeignKey('Song.SongID'))
    Position = Column(Integer)
    CreationDate = Column(DateTime, default=datetime.utcnow)
    playlist = relationship('Playlist', back_populates='songs')
    song = relationship('Song', back_populates='playlists')

class User_Rating(db.Model):
    __tablename__ = 'User_Rating'
    UserRatingID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey('User.UserID'))
    SongID = Column(Integer, ForeignKey('Song.SongID'))
    Rating = Column(Integer)
    Comments = Column(String) 
    CreationDate = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='ratings')
    song = relationship('Song', back_populates='ratings')

class Genre(db.Model):
    __tablename__ = 'Genre'
    GenreID = Column(Integer, primary_key=True)
    GenreName = Column(String)
    CreationDate = Column(DateTime, default=datetime.utcnow)

class Following(db.Model):
    __tablename__ = 'Following'
    FollowingID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey('User.UserID'))
    ArtistID = Column(Integer, ForeignKey('Artist.ArtistID'))
    CreationDate = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='followed_artists')
    artist = relationship('Artist', back_populates='followers')