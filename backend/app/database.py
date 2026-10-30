import sqlite3

from pathlib import Path


# Get the location of the backend folder.
BASE_DIR = Path(__file__).resolve().parent.parent

# Create the database file inside the backend folder.
DATABASE_PATH = BASE_DIR / "ogs.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection