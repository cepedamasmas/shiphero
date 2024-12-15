# modules/inventory_changes.py

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os
from modules.base import ShipHeroAPI
from utils.exceptions import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

class InventoryChanges(ShipHeroAPI):
    """
    Module for handling inventory changes in ShipHero.
    Inherits from ShipHeroAPI base class.
    """
    
    def __init__(self):
        """Initialize the InventoryChanges module."""
        super().__init__()
        self.logger.info("InventoryChanges module initialized")

    def _build_inventory_changes_query(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sku: Optional[str] = None,
        location_id: Optional[str] = None,
        first: int = 100,
        reason: Optional[str] = None
    ) -> str:
        """
        Build GraphQL query for inventory changes.
        
        Args:
            date_from (str, optional): Start date in ISO format
            date_to (str, optional): End date in ISO format
            sku (str, optional): Specific SKU to filter
            location_id (str, optional): Specific location ID to filter
            first (int): Number of records to fetch per page
            
        Returns:
            str: GraphQL query string
        """
        return """
        query($dateFrom: ISODateTime, $dateTo: ISODateTime, $sku: String, $locationId: String, $first: Int, $after: String, $reason: String) {
            inventory_changes(
                date_from: $dateFrom
                date_to: $dateTo
                sku: $sku
                location_id: $locationId
                reason: $reason
            ) {
                request_id
                complexity
                data (
                    first: $first
                    after: $after
                ) {
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }
                    edges {
                        node {
                            user_id
                            account_id
                            warehouse_id
                            sku
                            previous_on_hand
                            change_in_on_hand
                            reason
                            cycle_counted
                            location_id
                            created_at
                            location {
                                id
                                legacy_id
                                account_id
                                warehouse_id
                                name
                                zone
                                pickable
                                sellable
                                is_cart
                                temperature
                                last_counted
                                created_at
                            }
                        }
                        cursor
                    }
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

    def get_inventory_changes(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sku: Optional[str] = None,
        location_id: Optional[str] = None,
        reason: Optional[str] = None,
        max_records: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch inventory changes with pagination support.
        
        Args:
            date_from (str, optional): Start date in ISO format
            date_to (str, optional): End date in ISO format
            sku (str, optional): Specific SKU to filter
            location_id (str, optional): Specific location ID to filter
            max_records (int): Maximum number of records to fetch
            
        Returns:
            pd.DataFrame: DataFrame containing inventory changes
        """
        all_changes = []
        after_cursor = None
        records_fetched = 0
        page_size = min(100, max_records)
        
        query = self._build_inventory_changes_query()
        
        while records_fetched < max_records:
            variables = {
                "dateFrom": date_from,
                "dateTo": date_to,
                "sku": sku,
                "locationId": location_id,
                "first": page_size,
                "after": after_cursor,
                "reason": reason
            }
            
            response = self._make_request(query, variables)
            
            try:
                inventory_changes = response['data']['inventory_changes']
                inventory_changes_data = inventory_changes['data']
                if not inventory_changes_data:
                    break
                edges = inventory_changes_data['edges']
                
                if not edges:
                    break
                    
                # Flatten and collect records
                for edge in edges:
                    all_changes.append(self._flatten_inventory_change(edge['node']))
                    records_fetched += 1
                
                # Check pagination
                if not 'pageInfo' in inventory_changes_data:
                    break
                
                page_info = inventory_changes_data['pageInfo']
                if not page_info['hasNextPage']:
                    break
                    
                after_cursor = page_info['endCursor']
                
            except KeyError as e:
                self.logger.error(f"Unexpected response format: {str(e)}")
                raise ValidationError(f"Invalid response format: {str(e)}")
        
        df = pd.DataFrame(all_changes)  # Envolver en una lista para crear un DataFrame de una fila

        if len(all_changes) == 0:
            return df
        # Convertir el snapshot en un DataFrame
        
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df

    def export_to_csv(
        self,
        df: pd.DataFrame,
        prefix: str = "inventory_changes"
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