from app.database import engine
from app import models
from sqlalchemy import inspect

print("Creating tables with EXPLICIT commit...")
with engine.begin() as conn:
    models.Base.metadata.create_all(bind=conn)
print("Done, transaction committed.")

# Now check using a completely FRESH, separate connection/engine
from sqlalchemy import create_engine as ce
fresh_engine = ce("postgresql://postgres:admin@localhost:5432/ecommerce_db_fresh")
fresh_inspector = inspect(fresh_engine)
print("Tables found (fresh connection):", fresh_inspector.get_table_names())
