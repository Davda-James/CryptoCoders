from app import app  # Import your Flask app

if __name__ != "__main__":
    # This ensures the app is served by a WSGI server like Gunicorn or Waitress
    application = app