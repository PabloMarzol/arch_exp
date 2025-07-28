from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config
import os
from urllib.parse import quote_plus

# Get individual database components
DB_USER = config('DB_USER', default='postgres')
DB_PASSWORD = config('DB_PASSWORD', default='password')
DB_HOST = config('DB_HOST', default='localhost')
DB_PORT = config('DB_PORT', default='5432')
DB_NAME = config('DB_NAME', default='arch4_db')
TEST_DB_NAME = config('TEST_DB_NAME', default='arch4_test_db')

# URL encode the password to handle special characters
encoded_password = quote_plus(DB_PASSWORD)

# Construct URLs programmatically
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
TEST_DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"

# Use test database if we're in test mode
if os.getenv('TESTING'):
    engine = create_engine(TEST_DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()