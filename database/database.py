from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./titles.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Title model
class Title(Base):
    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    normalized_title = Column(String, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)
