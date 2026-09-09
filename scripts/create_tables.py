from sqlalchemy import text
from app.database import Base, engine, DATABASE_URL
from app import models  # noqa

print(f"Connecting to: {DATABASE_URL}")
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created. Listing tables:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';"))
    for row in result:
        print(row[0])