from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

# Cargar configuración desde .env
load_dotenv()

Base = declarative_base()

class Database:
    """
    Clase para gestionar la conexión a la base de datos MySQL.
    """

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL no está configurado en .env")

        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))

    @contextmanager
    def get_db(self):
        """
        Proporciona una sesión de base de datos.
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def init_db(self):
        """
        Inicializa las tablas en la base de datos.
        """
        Base.metadata.create_all(bind=self.engine)

    def insert_record(self, db_session, model, **kwargs):
        """
        Inserta un registro en la tabla especificada y devuelve el ID.

        Args:
            db_session: Sesión de base de datos activa.
            model: Clase del modelo SQLAlchemy que representa la tabla.
            **kwargs: Datos a insertar como pares clave-valor.

        Returns:
            int: ID del registro insertado.
        """
        try:
            new_record = model(**kwargs)
            db_session.add(new_record)
            db_session.commit()
            db_session.refresh(new_record)
            # Obtener la clave primaria del modelo
            primary_key = [getattr(new_record, key.name) for key in model.__mapper__.primary_key]
            
            # Si hay una sola clave, devolverla directamente
            return primary_key[0] if len(primary_key) == 1 else primary_key
        except SQLAlchemyError as e:
            db_session.rollback()
            raise Exception(f"Error al insertar el registro: {e}")