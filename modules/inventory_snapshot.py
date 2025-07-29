# modules/inventory_snapshot.py

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os
import requests
from modules.base import ShipHeroAPI
from utils.exceptions import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

class InventorySnapshot(ShipHeroAPI):
    """
    Module for handling inventory changes in ShipHero.
    Inherits from ShipHeroAPI base class.
    """
    
    def __init__(self):
        """Initialize the InventorySnapshot module."""
        super().__init__()
        self.logger.info("InventorySnapshot module initialized")

    def _build_abort_snapshot_mutation(self) -> str:
        """
        Build GraphQL mutation to abort a snapshot.

        Returns:
            str: GraphQL mutation string
        """
        return """
        mutation InventoryAbortSnapshot($snapshot_id: String!) {
        inventory_abort_snapshot(data: { snapshot_id: $snapshot_id }) {
    request_id
    complexity
    snapshot {
      snapshot_id
      job_user_id
      job_account_id
      warehouse_id
      customer_account_id
      notification_email
      email_error
      post_url
      post_error
      post_url_pre_check
      status
      error
      created_at
      enqueued_at
      updated_at
      snapshot_url
      snapshot_expiration
    }
  }
}
        """

    def abort_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Aborta un snapshot en ejecución.

        Args:
            snapshot_id (str): ID del snapshot a abortar.

        Returns:
            Dict[str, Any]: Respuesta de la API de ShipHero.

        Raises:
            ValidationError: Si la respuesta es inválida o si ocurre un error en la solicitud.
        """
        if not snapshot_id:
            raise ValidationError("Debe proporcionar un snapshot_id para abortar.")
        
        query = self._build_abort_snapshot_mutation()
        variables = {"snapshot_id": snapshot_id}

        try:
            response = self._make_request(query, variables)

            if "data" not in response or "inventory_abort_snapshot" not in response["data"]:
                self.logger.error("La respuesta de abort_snapshot es inválida.")
                raise ValidationError("Respuesta inválida al intentar abortar el snapshot.")
            
            result = response["data"]["inventory_abort_snapshot"]
            self.logger.info(f"Snapshot {snapshot_id} abortado correctamente.")
            return result

        except Exception as e:
            self.logger.error(f"Error al abortar snapshot: {e}")
            raise ValidationError(f"Fallo al abortar snapshot: {e}")

    def _build_inventory_snapshot_mutation(
        self
    ) -> str:
        """
        Build GraphQL query for inventory changes.
        
        Args:
            warehouse_id (str, optional): Specific warehouse_id to filter
            
        Returns:
            str: GraphQL query string
        """
        return """
    mutation InventoryGenerateSnapshot($warehouse_id: String!) {
      inventory_generate_snapshot(
        data: {
          warehouse_id: $warehouse_id
        }
      ) {
        request_id
        complexity
        snapshot {
          snapshot_id
          job_user_id
          job_account_id
          warehouse_id
          customer_account_id
          notification_email
          email_error
          post_url
          post_error
          post_url_pre_check
          status
          error
          created_at
          enqueued_at
          updated_at
          snapshot_url
          snapshot_expiration
        }
      }
    }
    """

    def _build_inventory_snapshot_query(
        self,
        snapshot_id: Optional[str] = None
    ) -> str:
        """
        Build GraphQL query for inventory changes.
        
        Args:
            snapshot_id (str, optional): Specific snapshot_id to filter
            
        Returns:
            str: GraphQL query string
        """
        return """
        query($snapshot_id: String!) {
  inventory_snapshot(snapshot_id: $snapshot_id) {
    request_id
    complexity
    snapshot {
      snapshot_id
      job_user_id
      job_account_id
      warehouse_id
      customer_account_id
      notification_email
      email_error
      post_url
      post_error
      post_url_pre_check
      status
      error
      created_at
      enqueued_at
      updated_at
      snapshot_url
      snapshot_expiration
    }
  }
}
        """

    def _flatten_inventory_change(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten a single inventory change record.
        
        Args:
            node (Dict[str, Any]): Raw inventory change node
            
        Returns:
            Dict[str, Any]: Flattened record
        """
        location = node.get('location', {})
        
        return {
            'user_id': node.get('user_id'),
            'account_id': node.get('account_id'),
            'warehouse_id': node.get('warehouse_id'),
            'sku': node.get('sku'),
            'previous_on_hand': node.get('previous_on_hand'),
            'change_in_on_hand': node.get('change_in_on_hand'),
            'current_on_hand': (node.get('previous_on_hand', 0) + 
                              node.get('change_in_on_hand', 0)),
            'reason': node.get('reason'),
            'cycle_counted': node.get('cycle_counted'),
            'location_id': node.get('location_id'),
            'created_at': node.get('created_at'),
            'location_name': location.get('name'),
            'location_zone': location.get('zone'),
            'location_pickable': location.get('pickable'),
            'location_sellable': location.get('sellable'),
            'location_temperature': location.get('temperature'),
            'location_last_counted': location.get('last_counted')
        }

    def generate_snapshot(self, warehouse_id: str) -> pd.DataFrame:
        """
        Obtiene un snapshot de inventario y procesa la respuesta en un DataFrame.
        
        Args:
            warehouse_id (str): ID del almacén para generar un snapshot.
        
        Returns:
            pd.DataFrame: DataFrame con los detalles del snapshot.
        
        Raises:
            ValidationError: Si el formato de la respuesta es inválido o contiene un error.
        """
        query = self._build_inventory_snapshot_mutation()
        variables = {"warehouse_id": warehouse_id}
        
        try:
            response = self._make_request(query, variables)
            
            # Validar las claves principales de la respuesta
            if "data" not in response:
                self.logger.error("La respuesta no contiene la clave 'data'.")
                raise ValidationError("Formato de respuesta inválido: Falta la clave 'data'.")
            
            data = response["data"]
            if "inventory_generate_snapshot" not in data:
                self.logger.error("La respuesta no contiene la clave 'inventory_generate_snapshot'.")
                raise ValidationError("Formato de respuesta inválido: Falta la clave 'inventory_generate_snapshot'.")
            
            snapshot_data = data["inventory_generate_snapshot"]
            
            # Validar la estructura del snapshot
            if "snapshot" not in snapshot_data or not isinstance(snapshot_data["snapshot"], dict):
                self.logger.error("Los datos del snapshot están ausentes o mal formateados.")
                raise ValidationError("Formato de respuesta inválido: Falta la clave 'snapshot' o no es válida.")
            
            snapshot = snapshot_data["snapshot"]
            
            if snapshot["snapshot_id"] is None:
                self.logger.error("Error al no obtener el snapshot_id.")
                raise ValidationError("Formato de respuesta inválido: Falta la clave 'snapshot_id' o no es válida.")
            
            self.logger.info("El snapshot se recuperó correctamente y se devolvio el snapshot_id")
            return snapshot["snapshot_id"]
        
        except KeyError as e:
            self.logger.error(f"Estructura inesperada en la respuesta: {str(e)}")
            raise ValidationError(f"Formato de respuesta inválido: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Ocurrió un error durante la generación del snapshot: {str(e)}")
            raise ValidationError(f"Fallo en la generación del snapshot: {str(e)}")

        
        except KeyError as e:
            self.logger.error(f"Unexpected response structure: {str(e)}")
            raise ValidationError(f"Invalid response format: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"An error occurred during snapshot generation: {str(e)}")
            raise ValidationError(f"Snapshot generation failed: {str(e)}")

        
    def get_snapshot_by_id(self, snapshot_id: str) -> pd.DataFrame:
        """
        Obtiene el estado actual del inventario basado en el ID del snapshot.
        
        Args:
            snapshot_id (str): ID específico del snapshot para consultar.
        
        Returns:
            pd.DataFrame: DataFrame con los detalles del snapshot.
        
        Raises:
            ValidationError: Si el formato de la respuesta es inválido o contiene un error.
        """
        if not snapshot_id:
            self.logger.error("Debe ingresar un ID de snapshot.")
            raise ValidationError("El ID de snapshot es obligatorio.")
        
        query = self._build_inventory_snapshot_query()
        variables = {"snapshot_id": snapshot_id}
        
        try:
            response = self._make_request(query, variables)
            
            # Validar las claves principales de la respuesta
            if "data" not in response:
                self.logger.error("La respuesta no contiene la clave 'data'.")
                raise ValidationError("Formato de respuesta inválido: Falta la clave 'data'.")
            
            data = response["data"]
            if "inventory_snapshot" not in data:
                self.logger.error("La respuesta no contiene la clave 'inventory_snapshot'.")
                raise ValidationError("Formato de respuesta inválido: Falta la clave 'inventory_snapshot'.")
            
            snapshot_data = data["inventory_snapshot"]
            
            # Validar la estructura del snapshot
            if "snapshot" not in snapshot_data or not isinstance(snapshot_data["snapshot"], dict):
                self.logger.error("Los datos del snapshot están ausentes o mal formateados.")
                raise ValidationError("Formato de respuesta inválido: Falta la clave 'snapshot' o no es válida.")
            
            snapshot = snapshot_data["snapshot"]
            
            # Convertir el snapshot en un DataFrame
            df = pd.DataFrame([snapshot])  # Envolver en una lista para crear un DataFrame de una fila
            
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['enqueued_at'] = pd.to_datetime(df['enqueued_at'])
            df['updated_at'] = pd.to_datetime(df['updated_at'])
            
            # Registrar éxito y devolver el DataFrame
            self.logger.info("El snapshot se recuperó correctamente y se convirtió en un DataFrame.")
            return df
        
        except KeyError as e:
            self.logger.error(f"Estructura inesperada en la respuesta: {str(e)}")
            raise ValidationError(f"Formato de respuesta inválido: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Ocurrió un error al obtener el snapshot: {str(e)}")
            raise ValidationError(f"Fallo al obtener el snapshot: {str(e)}")

        
    def get_inventory(
        self
    ) -> str:
        """
        Get current inventory status with pagination support.
        
        Args:
            snapshot_id (str, optional): Specific snapshot to query
            
        Returns:
            pd.DataFrame: Current inventory status
        """
        
        query = self._build_inventory_snapshot_query()
    
        variables = {
            "snapshot_id": snapshot_id
        }
        snapshot_url = None
        try:
            response = self._make_request(query, variables)
            snapshot_url = response.get('data', {}).get('inventory_snapshot', {}).get('snapshot', {}).get('snapshot_url')
            if snapshot_url is None:
                raise ValueError("La propiedad 'snapshot_url' no está presente o es nula.")
            
        except KeyError as e:
            self.logger.error(f"Unexpected response format: {str(e)}")
            raise ValidationError(f"Invalid response format: {str(e)}")
            
        return snapshot_url
        
    def get_inventory_snapshot_by_url(
        self,
        snapshot_url: str
    ) -> str:
        """
        Get current inventory status with pagination support.
        
        Args:
            snapshot_url (str, optional): url donde esta alojado el json del inventario
            
        Returns:
            pd.DataFrame: Current inventory status
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.get(snapshot_url, headers=headers, timeout=100)
            response.raise_for_status()  # Levanta una excepción si el status code no es 200-299

            # Intenta parsear la respuesta como JSON
            snapshot_json = response.json()

            return self.flatten_inventory_snapshot(snapshot_json)

        except requests.exceptions.Timeout:
            self.logger.error("Error: La solicitud excedió el tiempo de espera.")
            raise ValidationError("Error: La solicitud excedió el tiempo de espera.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error al realizar la solicitud POST: {e}")
            raise ValidationError(f"Error al realizar la solicitud POST: {e}")
        except ValueError:
            self.logger.error(f"Error: No se pudo parsear la respuesta como JSON")
            raise ValidationError(f"Error: No se pudo parsear la respuesta como JSON")
        
        return None
    
    def flatten_inventory_snapshot(self,snapshot_json: dict) -> pd.DataFrame:
        """
        Convierte un JSON de inventario anidado en un DataFrame plano.

        Args:
            snapshot_json (dict): Respuesta JSON del snapshot.

        Returns:
            pd.DataFrame: DataFrame con la información del inventario.
        """
        flattened_data = []

        # Extraer el ID del snapshot y detalles generales
        snapshot_id = snapshot_json.get("snapshot_id", "")
        warehouse_id = snapshot_json.get("warehouse_id", "")
        snapshot_started_at = snapshot_json.get("snapshot_started_at", "")
        snapshot_finished_at = snapshot_json.get("snapshot_finished_at", "")

        # Procesar los productos
        products = snapshot_json.get("products", {})
        for sku, product_data in products.items():
            account_id = product_data.get("account_id", "")
            vendors = product_data.get("vendors", {})
            
            # Procesar warehouse_products
            warehouse_products = product_data.get("warehouse_products", {})
            for warehouse_id, warehouse_data in warehouse_products.items():
                on_hand = warehouse_data.get("on_hand", 0)
                allocated = warehouse_data.get("allocated", 0)
                backorder = warehouse_data.get("backorder", 0)
                available = warehouse_data.get("available", 0)
                reserve = warehouse_data.get("reserve", 0)
                non_sellable = warehouse_data.get("non_sellable", 0)
                flattened_data.append({
                        "snapshot_id": snapshot_id,
                        "warehouse_id": warehouse_id,
                        "snapshot_started_at": snapshot_started_at,
                        "snapshot_finished_at": snapshot_finished_at,
                        "sku": sku,
                        "account_id": account_id,
                        "vendor_id": "",
                        "vendor_name": "",
                        "on_hand": on_hand,
                        "allocated": allocated,
                        "backorder": backorder,
                        "available": available,
                        "reserve": reserve,
                        "non_sellable": non_sellable
                    })
                # Procesar item_bins
                """item_bins = warehouse_data.get("item_bins", {})
                for bin_id, bin_data in item_bins.items():
                    location_id = bin_data.get("location_id", "")
                    location_name = bin_data.get("location_name", "")
                    lot_id = bin_data.get("lot_id", "")
                    lot_name = bin_data.get("lot_name", "")
                    expiration_date = bin_data.get("expiration_date", "")
                    sellable = bin_data.get("sellable", False)
                    quantity = bin_data.get("quantity", 0)

                    # Agregar fila al DataFrame
                    flattened_data.append({
                        "snapshot_id": snapshot_id,
                        "warehouse_id": warehouse_id,
                        "snapshot_started_at": snapshot_started_at,
                        "snapshot_finished_at": snapshot_finished_at,
                        "sku": sku,
                        "account_id": account_id,
                        "vendor_id": vendors.get("vendor_id", ""),
                        "vendor_name": vendors.get("vendor_name", ""),
                        "on_hand": on_hand,
                        "allocated": allocated,
                        "backorder": backorder,
                        "available": available,
                        "reserve": reserve,
                        "non_sellable": non_sellable,
                        "location_id": location_id,
                        "location_name": location_name,
                        "lot_id": lot_id,
                        "lot_name": lot_name,
                        "expiration_date": expiration_date,
                        "sellable": sellable,
                        "quantity": quantity,
                    })

                # Si no hay bins, agregar una fila base
                if not item_bins:
                    flattened_data.append({
                        "snapshot_id": snapshot_id,
                        "warehouse_id": warehouse_id,
                        "snapshot_started_at": snapshot_started_at,
                        "snapshot_finished_at": snapshot_finished_at,
                        "sku": sku,
                        "account_id": account_id,
                        "vendor_id": "",
                        "vendor_name": "",
                        "on_hand": on_hand,
                        "allocated": allocated,
                        "backorder": backorder,
                        "available": available,
                        "reserve": reserve,
                        "non_sellable": non_sellable,
                        "location_id": "",
                        "location_name": "",
                        "lot_id": "",
                        "lot_name": "",
                        "expiration_date": "",
                        "sellable": "",
                        "quantity": "",
                    })"""

        # Convertir los datos planos a un DataFrame
        df = pd.DataFrame(flattened_data)
        df['snapshot_started_at'] = pd.to_datetime(df['snapshot_started_at'])
        df['snapshot_finished_at'] = pd.to_datetime(df['snapshot_finished_at'])
        return df

    def export_to_csv(
        self,
        df: pd.DataFrame,
        prefix: str = "inventory_snapshot"
    ) -> str:
        """
        Export inventory changes to CSV file.
        
        Args:
            df (pd.DataFrame): DataFrame to export
            prefix (str): Prefix for the CSV filename
            
        Returns:
            str: Path to the generated CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.csv"
        
        # Ensure output directory exists
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        
        filepath = os.path.join(self.config.OUTPUT_DIR, filename)
        
        df.to_csv(
            filepath,
            sep=self.config.CSV_SEPARATOR,
            encoding=self.config.CSV_ENCODING,
            index=False
        )
        
        self.logger.info(f"Exported {len(df)} records to {filepath}")
        return filepath
    
    def insert_df_to_db(self,df,nombre_tabla):
        if not nombre_tabla:
            raise ValidationError(f"Se necesita un nombre de tabla")
        
        # Configura la conexión a la base de datos
        DATABASE_URI = os.getenv("DATABASE_URL")
    
        self.logger.info(f"Abriendo conexion a DB")
        # Crear una conexión usando SQLAlchemy
        engine = create_engine(DATABASE_URI)
        
        # Inicia una transacción
        with engine.begin():
            try:
                # Inserta los datos en la base de datos, usando chunksize para manejar grandes volúmenes de datos
                df.to_sql(nombre_tabla, con=engine, if_exists="append", index=False, chunksize=1000)
                self.logger.info("Datos insertados exitosamente en la tabla.")
            
            except SQLAlchemyError as e:
                # Manejo de errores en SQLAlchemy
                self.logger.error(f"Error al insertar los datos: {e}")
                raise ValidationError(f"Error al insertar los datos: {e}")
            except Exception as e:
                # Manejo de otros errores
                self.logger.error(f"Error inesperado: {e}")
                raise ValidationError(f"Error inesperado: {e}")