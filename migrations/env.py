import os
from dotenv import load_dotenv
from alembic import context
from sqlalchemy import create_engine
from app.knowledge.database import metadata

load_dotenv()
config = context.config
url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
if context.is_offline_mode():
    context.configure(url=url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = config.attributes.get("connection")

    def run(conn):
        context.configure(connection=conn, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()

    if connection is not None:
        run(connection)
    else:
        with create_engine(url).connect() as conn:
            run(conn)
