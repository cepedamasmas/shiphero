from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from sqlalchemy.sql import text

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
        
    def get_max_created_at(self, db_session, model):
        """
        Obtiene el valor máximo de created_at de la tabla sph_transacciones.

        Args:
            db_session: Sesión activa de la base de datos.

        Returns:
            datetime: El valor máximo de created_at.
        """
        try:
            # Realizamos la consulta para obtener el máximo de created_at
            max_created_at = db_session.query(func.max(model.created_at)).scalar()
            return max_created_at
        except SQLAlchemyError as e:
            db_session.rollback()
            raise Exception(f"Error al obtener el valor máximo de created_at: {e}")
        
    def execute_stored_procedure(self, db_session, procedure_name, params=None):
        """
        Ejecuta un procedimiento almacenado en la base de datos.

        Args:
            db_session: Sesión activa de la base de datos.
            procedure_name (str): Nombre del procedimiento almacenado.
            params (list, optional): Lista de parámetros para el procedimiento almacenado.

        Returns:
            list: Resultados de la ejecución del procedimiento almacenado.
        """
        try:
            # Construir la llamada al procedimiento almacenado
            param_placeholders = ", ".join([":p" + str(i) for i in range(len(params))]) if params else ""
            query = text(f"CALL {procedure_name}({param_placeholders})")

            # Crear un diccionario de parámetros
            param_dict = {f"p{i}": param for i, param in enumerate(params or [])}

            # Ejecutar el procedimiento almacenado
            result = db_session.execute(query, param_dict)
            
            # Si el procedimiento devuelve resultados, los obtenemos
            if result.returns_rows:
                return result.fetchall()
            return None
        except SQLAlchemyError as e:
            db_session.rollback()
            raise Exception(f"Error al ejecutar el procedimiento almacenado '{procedure_name}': {e}")
