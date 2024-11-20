# modules/inventory_status.py

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os
from modules.base import ShipHeroAPI
from utils.exceptions import ValidationError

class InventoryStatus(ShipHeroAPI):
    """
    Module for querying current inventory status in ShipHero.
    """
    
    def __init__(self):
        """Initialize the InventoryStatus module."""
        super().__init__()
        self.logger.info("InventoryStatus module initialized")

    def _build_inventory_query(
        self,
        sku: Optional[str] = None,
        first: int = 100
    ) -> str:
        """
        Build GraphQL query for inventory status.
        
        Args:
            sku (str, optional): Specific SKU to query
            first (int): Number of records to fetch per page
            
        Returns:
            str: GraphQL query
        """
        return """
        query($sku: String, $first: Int!, $after: String) {
            inventory(
                sku: $sku
                first: $first
                after: $after
            ) {
                request_id
                complexity
                page_info {
                    has_next_page
                    end_cursor
                }
                edges {
                    node {
                        id
                        sku
                        warehouse_products {
                            warehouse_id
                            on_hand
                            available
                            reserved
                            replenishable
                            warehouse {
                                name
                                legacy_id
                            }
                        }
                        product {
                            name
                            barcode
                            vendor_sku
                            retail_price
                            wholesale_price
                        }
                    }
                }
            }
        }
        """

    def _flatten_inventory_record(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten a single inventory record.
        
        Args:
            node (Dict[str, Any]): Raw inventory node
            
        Returns:
            List[Dict[str, Any]]: List of flattened warehouse records
        """
        flattened_records = []
        product = node.get('product', {})
        
        for warehouse_product in node.get('warehouse_products', []):
            warehouse = warehouse_product.get('warehouse', {})
            
            record = {
                'sku': node.get('sku'),
                'product_id': node.get('id'),
                'product_name': product.get('name'),
                'barcode': product.get('barcode'),
                'vendor_sku': product.get('vendor_sku'),
                'retail_price': product.get('retail_price'),
                'wholesale_price': product.get('wholesale_price'),
                'warehouse_id': warehouse_product.get('warehouse_id'),
                'warehouse_name': warehouse.get('name'),
                'warehouse_legacy_id': warehouse.get('legacy_id'),
                'on_hand': warehouse_product.get('on_hand', 0),
                'available': warehouse_product.get('available', 0),
                'reserved': warehouse_product.get('reserved', 0),
                'replenishable': warehouse_product.get('replenishable', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            flattened_records.append(record)
            
        return flattened_records

    def get_inventory_status(
        self,
        sku: Optional[str] = None,
        max_records: int = 1000
    ) -> pd.DataFrame:
        """
        Get current inventory status with pagination support.
        
        Args:
            sku (str, optional): Specific SKU to query
            max_records (int): Maximum number of records to fetch
            
        Returns:
            pd.DataFrame: Current inventory status
        """
        all_records = []
        after_cursor = None
        records_fetched = 0
        page_size = min(100, max_records)
        
        query = self._build_inventory_query()
        
        while records_fetched < max_records:
            variables = {
                "sku": sku,
                "first": page_size,
                "after": after_cursor
            }
            
            try:
                response = self._make_request(query, variables)
                inventory_data = response['data']['inventory']
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

    def export_inventory_status(
        self,
        df: pd.DataFrame,
        prefix: str = "inventory_status"
    ) -> str:
        """
        Export inventory status to CSV.
        
        Args:
            df (pd.DataFrame): DataFrame with inventory status
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
        
        self.logger.info(f"Exported inventory status to {filepath}")
        return filepath

    def get_low_stock_items(
        self,
        threshold: int = 10
    ) -> pd.DataFrame:
        """
        Get items with stock below specified threshold.
        
        Args:
            threshold (int): Stock threshold
            
        Returns:
            pd.DataFrame: Low stock items
        """
        df = self.get_inventory_status()
        low_stock = df[df['available'] <= threshold].copy()
        
        if not low_stock.empty:
            self.logger.warning(f"Found {len(low_stock)} items with low stock")
            
        return low_stock.sort_values('available')