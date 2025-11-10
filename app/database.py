# app/database.py
import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

# 1) Load .env first
load_dotenv(find_dotenv())

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Put it in a .env file at project root or set it in the environment."
    )

# 2) Ensure the database exists (create if missing)
url = make_url(DATABASE_URL)

# connect to server without selecting a database
server_url = url.set(database=None)          # works for mysql+mysqlconnector
# server_url = url.set(database="mysql")     # alternative if your server forbids no-DB connections

_tmp_engine = create_engine(server_url, pool_pre_ping=True, future=True)
with _tmp_engine.connect() as conn:
    conn.execute(text(
        f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    ))
    conn.commit()
_tmp_engine.dispose()

# 3) Normal engine/session/Base for your app
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# 4) Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()