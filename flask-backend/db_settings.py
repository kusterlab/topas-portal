from peewee import PostgresqlDatabase
import os


DATABASE = {
    "HOST": os.getenv("DB_HOST", "db"),
    "PORT": os.getenv("DB_PORT", 5432),
    "NAME": os.getenv("DB_NAME", "cohort_db"),
    "USER": os.getenv("DB_USER", "topas"),
    "PASSWORD": os.getenv("DB_PASSWORD"),
}


db = PostgresqlDatabase(
    DATABASE["NAME"],
    user=DATABASE["USER"],
    password=DATABASE["PASSWORD"],
    host=DATABASE["HOST"],
    port=DATABASE["PORT"],
    sslmode="disable",
)
