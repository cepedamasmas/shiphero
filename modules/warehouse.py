# modules/warehouse.py

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os
from modules.base import ShipHeroAPI
from utils.exceptions import ValidationError

class Warehouse(ShipHeroAPI):
    """
    Module for managing product kits in ShipHero.
    """
    
    def __init__(self):
        """Initialize the Products module."""
        super().__init__()
        self.logger.info("Products module initialized")

    def _build_account_query(self) -> str:
        """
        Build GraphQL query to get kit information.
        
        Args:
            sku (str): Kit SKU
            
        Returns:
            str: GraphQL query
        """
        return """
        query {
  account {
    complexity
    request_id
    data {
      id
      legacy_id
      email
      username
      status
      is_3pl
      warehouses {
        id
        legacy_id
        identifier
        invoice_email
        profile
        address {
          name
        }
      }
    }
  }
} 
        """
    def _build_warehouse_products_query(
        self,
        warehouse_id: Optional[str] = None
    ) -> str:
        """
        Build GraphQL query to get kit information.
        
        Args:
            warehouse_id (str): Id del warehouse
            
        Returns:
            str: GraphQL query
        """
        return """
        query($warehouse_id: String) {
  warehouse_products(warehouse_id: $warehouse_id) {
    request_id
    complexity
    data(first: 2) {
      edges {
        node {
          id
          account_id
          on_hand
          inventory_bin
          reserve_inventory
          reorder_amount
          reorder_level
          custom
          warehouse {
            id
            dynamic_slotting
            profile
          }
          product {
            id
            name
            sku
          }
        }
        cursor
      }
    }
  }
}
        """

    def get_warehouses(self) -> pd.DataFrame:
        """
        Get detailed information about a kit and its components.
        
        Args:
            sku (str): SKU
            
        Returns:
            pd.DataFrame: Kit components details
        """
        query = self._build_account_query()
        
        try:
            response = self._make_request(query)
            
            warehouses_data = []
            account_data = response.get('data', {}).get('account', {}).get('data', {})
            warehouses = account_data.get('warehouses', [])
            if not warehouses:
                raise ValueError("No se encontraron datos de 'warehouses'.")

            for warehouse in warehouses:
                if warehouse.get('id') != 'V2FyZWhvdXNlOjc3MTQ4':
                    warehouse_detail = {
                        'warehouse_id': warehouse.get('id'),
                        'legacy_id': warehouse.get('legacy_id'),
                        'identifier': warehouse.get('identifier'),
                        'invoice_email': warehouse.get('invoice_email'),
                        'profile': warehouse.get('profile'),
                        'address_name': warehouse.get('address', {}).get('name'),
                        'account_email': account_data.get('email')  # Datos adicionales si se necesitan
                    }
                    warehouses_data.append(warehouse_detail)
            
            return pd.DataFrame(warehouses_data)
            
        except Exception as e:
            self.logger.error(f"{str(e)}")
            raise
        
    def get_warehouse_products(
        self,
        warehouse_id: str,
        max_records: int = 1000
    ) -> pd.DataFrame:
        """
        Get current inventory status with pagination support.
        
        Args:
            warehouse_id (str, optional): Specific warehouse to query
            max_records (int): Maximum number of records to fetch
            
        Returns:
            pd.DataFrame: Current inventory status
        """
        if not warehouse_id:
            self.logger.error(f"Necesita ingresar un warehouse id")
            return False
        all_records = []
        after_cursor = None
        records_fetched = 0
        page_size = min(100, max_records)
        
        query = self._build_warehouse_products_query()
        
        while records_fetched < max_records:
            variables = {
                "warehouse_id": warehouse_id,
                "first": page_size,
                "after": after_cursor
            }
            
            try:
                response = self._make_request(query, variables)
                data = response['data']
                print(data)
                exit()
                edges = inventory_data['edges']
                
                if not edges:
                    break
                
                # Process and flatten records
                for edge in edges:
                    flattened_records = self._flatten_inventory_record(edge['node'])
                    all_records.extend(flattened_records)
                    records_fetched += 1
                
                # Check pagination
                page_info = inventory_data['page_info']
                if not page_info['has_next_page']:
                    break
                    
                after_cursor = page_info['end_cursor']
                
            except KeyError as e:
                self.logger.error(f"Unexpected response format: {str(e)}")
                raise ValidationError(f"Invalid response format: {str(e)}")
            
        return pd.DataFrame(all_records)



    def export_to_csv(
        self,
        df: pd.DataFrame,
        prefix: str = "warehouse_products"
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