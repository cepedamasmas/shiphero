# modules/kits_manager.py

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os
from modules.base import ShipHeroAPI
from utils.exceptions import ValidationError

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

    def export_kit_details(
        self,
        df: pd.DataFrame,
        prefix: str = "kit_details"
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