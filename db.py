
import os
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float
from databases import Database

# Leer URL de conexión desde variable de entorno o usar valor por defecto
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://patrullaje_db_user:XxzmVTp4zSKZGDPnrCwm7sbXGUuB5tPZ@dpg-d08jq0nfte5s73eb7s4g-a/patrullaje_db")

# Inicializar el motor y base de datos
database = Database(DATABASE_URL)
metadata = MetaData()

# Definir tabla rutas
rutas = Table(
    "rutas",
    metadata,
    Column("latitud", Float),
    Column("longitud", Float),
    Column("fecha_hora", String),
    Column("tipo", String),
    Column("cedula", String),
)

# Crear tabla si no existe (solo una vez)
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)
