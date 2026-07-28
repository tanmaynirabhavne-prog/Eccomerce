from app.database import engine
from app import models

print("Creating tables...")
models.Base.metadata.create_all(bind=engine)
print("Done. Tables should now exist.")

from sqlalchemy import inspect
inspector = inspect(engine)
print("Tables found:", inspector.get_table_names())
