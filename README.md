# Vybe

#### A Music Streaming Application

## Overview

A feature-rich music streaming application built with Flask, SQLite, and SQLAlchemy.

## Features

- User authentication and registration
- Artist following and user playlists
- Song rating and commenting
- Search functionality for songs, albums, and artists
- Admin panel for CRUD operations on users, artists, albums, and songs
- Detailed statistics on the admin dashboard
- RESTful API for CRUD operations on songs, playlists, and albums

## Technologies Used

- **Backend**: Flask, SQLite, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **API**: Flask-Restful
- **ORM Tool**: SQLAlchemy

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/your-username/music-streaming-app.git
cd music-streaming-app
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up the database:

```bash
python setup_db.py
```

4. Run the application:

```bash
python main.py
```

Visit `http://localhost:8080` in your web browser.

## Usage

- Sign up for an account or log in if you already have one.
- Explore the music library, search for your favorite songs, albums, or artists.
- Follow artists to receive updates on their latest releases.
- Create playlists and add your favorite songs.
- Rate and comment on songs to share your feedback.

## Admin Panel

The admin panel is accessible at `/admin`. Log in with admin credentials to perform CRUD operations on users, artists, albums, and songs.

## API Endpoints

- `/api/songs`: GET, POST
- `/api/songs/<int:song_id>`: GET, PUT, DELETE
- `/api/albums`: GET, POST
- `/api/albums/<int:album_id>`: GET, PUT, DELETE
- `/api/playlists`: GET, POST
- `/api/playlists/<int:playlist_id>`: GET, PUT, DELETE

Explore the [API documentation](link_to_api_docs) for more details.

## Statistics

View application statistics at `/api/statistics`.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.
