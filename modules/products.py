# modules/kits_manager.py

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os
from modules.base import ShipHeroAPI
from utils.exceptions import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

class Products(ShipHeroAPI):
    """
    Module for managing product kits in ShipHero.
    """
    
    def __init__(self):
        """Initialize the Products module."""
        super().__init__()
        self.logger.info("Products module initialized")

    def _build_kit_query(self, sku: str) -> str:
        """
        Build GraphQL query to get kit information.
        
        Args:
            sku (str): Kit SKU
            
        Returns:
            str: GraphQL query
        """
        return """
        query {
  products {
    request_id
    complexity
    data {
      edges {
        node {
          id
          legacy_id
          account_id
          name
          sku
          barcode
          country_of_manufacture
          dimensions {
            height
            width
            length
            weight
          }
          tariff_code
          kit
          kit_build
          no_air
          final_sale
          customs_value
          customs_description
          not_owned
          dropship
          needs_serial_number
          thumbnail
          large_thumbnail
          created_at
          updated_at
          product_note
          virtual
          ignore_on_invoice
          ignore_on_customs
          active
          warehouse_products {
            warehouse_id
            on_hand
          }
          images {
            src
          }
          tags
          kit_components {
            sku
            quantity
          }
        }
      }
    }
  }
}
        """

    def _build_product_query(self) -> str:
        """
        Build GraphQL query to get kit information.
        
        Returns:
            str: GraphQL query
        """
        return """
        query($first: Int, $after: String, $has_kits: Boolean) {
  products(has_kits: $has_kits) {
    request_id
    complexity
    data(
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
          id
          legacy_id
          account_id
          name
          sku
          barcode
          country_of_manufacture
          dimensions {
            height
            width
            length
            weight
          }
          tariff_code
          kit
          kit_build
          no_air
          final_sale
          customs_value
          customs_description
          not_owned
          dropship
          needs_serial_number
          thumbnail
          large_thumbnail
          created_at
          updated_at
          product_note
          virtual
          ignore_on_invoice
          ignore_on_customs
          active
          warehouse_products {
            warehouse_id
            on_hand
          }
          images {
            src
          }
          tags
          kit_components {
            sku
            quantity
          }
        }
      cursor
      }
    }
  }
}
        """
    def flatten_product_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
      """
      Flattens the product node structure into a single dictionary for easier handling.
      """
      flattened_node = {
          "id": node.get("id"),
          "legacy_id": node.get("legacy_id"),
          "account_id": node.get("account_id"),
          "name": node.get("name"),
          "sku": node.get("sku"),
          "barcode": node.get("barcode"),
          "country_of_manufacture": node.get("country_of_manufacture"),
          "tariff_code": node.get("tariff_code"),
          "kit": node.get("kit"),
          "final_sale": node.get("final_sale"),
          "customs_value": node.get("customs_value"),
          "thumbnail": node.get("thumbnail"),
          "created_at": node.get("created_at"),
          "updated_at": node.get("updated_at"),
          "active": node.get("active"),
          # Flatten warehouse products
          "warehouse_products": [
              {"warehouse_id": wp.get("warehouse_id"), "on_hand": wp.get("on_hand")}
              for wp in node.get("warehouse_products", [])
          ],
          # Collect image URLs
          "images": [img.get("src") for img in node.get("images", [])],
          # Collect tags
          "tags": node.get("tags", []),
          # Flatten kit components
          "kit_components": [
              {"sku": kc.get("sku"), "quantity": kc.get("quantity")}
              for kc in node.get("kit_components", [])
          ]
      }
      return flattened_node

    def get_products_details(self, sku: str) -> pd.DataFrame:
        """
        Get detailed information about a kit and its components.
        
        Args:
            sku (str): SKU
            
        Returns:
            pd.DataFrame: Kit components details
        """
        query = self._build_kit_query(sku)
        variables = {"sku": sku}
        
        try:
            response = self._make_request(query, variables)
            print(response)
            exit()
            product_data = response['data']['product']
            
            if not product_data:
                raise ValidationError(f"Kit {sku} not found")
            
            components_data = []
            for component in product_data.get('components', []):
                component_detail = {
                    'sku': sku,
                    'kit_name': product_data.get('name'),
                    'component_sku': component.get('sku'),
                    'component_name': component.get('product', {}).get('name'),
                    'quantity': component.get('quantity'),
                    'component_id': component.get('id')
                }
                components_data.append(component_detail)
            
            return pd.DataFrame(components_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching kit details for {sku}: {str(e)}")
            raise


    def get_all_kits(self,
        max_records: int = 20
        ) -> pd.DataFrame:
        """
        Get all products
        
        Returns:
            pd.DataFrame: Products details
        """
    
        all_changes = []
        after_cursor = None
        records_fetched = 0
        page_size = min(10, max_records)
        
        query = self._build_product_query()
        
        while records_fetched < max_records:
            variables = {
                "has_kits": True,
                "first": page_size,
                "after": after_cursor
            }
            
            response = self._make_request(query, variables)
            
            try:
                products = response['data']['products']
                products_data = products['data']
                if not products_data:
                    break
                edges = products_data['edges']
                
                if not edges:
                    break
                    
                # Flatten and collect records
                for edge in edges:
                    all_changes.append(self.flatten_product_node(edge['node']))
                    records_fetched += 1
                
                # Check pagination
                if not 'pageInfo' in products_data:
                    break
                
                page_info = products_data['pageInfo']
                if not page_info['hasNextPage']:
                    break
                    
                after_cursor = page_info['endCursor']
                
            except KeyError as e:
                self.logger.error(f"Unexpected response format: {str(e)}")
                raise ValidationError(f"Invalid response format: {str(e)}")
        
        return pd.DataFrame(all_changes)

    def get_all(self,
        max_records: int = 99999
        ) -> pd.DataFrame:
        """
        Get all products
        
        Returns:
            pd.DataFrame: Products details
        """
    
        all_changes = []
        after_cursor = None
        records_fetched = 0
        page_size = min(200, max_records)
        
        query = self._build_product_query()
        
        while records_fetched < max_records:
            variables = {
                "first": page_size,
                "after": after_cursor
            }
            
            response = self._make_request(query, variables)
            
            try:
                products = response['data']['products']
                products_data = products['data']
                if not products_data:
                    break
                edges = products_data['edges']
                
                if not edges:
                    break
                    
                # Flatten and collect records
                for edge in edges:
                    all_changes.append(self.flatten_product_node(edge['node']))
                    records_fetched += 1
                
                # Check pagination
                if not 'pageInfo' in products_data:
                    break
                
                page_info = products_data['pageInfo']
                if not page_info['hasNextPage']:
                    break
                    
                after_cursor = page_info['endCursor']
                
            except KeyError as e:
                self.logger.error(f"Unexpected response format: {str(e)}")
                raise ValidationError(f"Invalid response format: {str(e)}")
        
        return pd.DataFrame(all_changes)

    def export_to_csv(
        self,
        df: pd.DataFrame,
        prefix: str = "products"
    ) -> str:
        """
        Export kit details to CSV.
        
        Args:
            df (pd.DataFrame): DataFrame with kit details
            prefix (str): Prefix for the filename
            
        Returns:
            str: Path to the generated CSV file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.csv"
        
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(self.config.OUTPUT_DIR, filename)
        
        df.to_csv(
            filepath,
            sep=self.config.CSV_SEPARATOR,
            encoding=self.config.CSV_ENCODING,
            index=False
        )
        
        self.logger.info(f"Exported kit details to {filepath}")
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