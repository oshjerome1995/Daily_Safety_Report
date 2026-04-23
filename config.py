import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
DATABASE = os.path.join(BASE_DIR, "database.db")