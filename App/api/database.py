# © 2025 NTT DATA Japan Co., Ltd. & NTT InfraNet All Rights Reserved.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
# DATABASE_URL = "postgresql://postgres:postgres@db:5432/postgres"



engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
