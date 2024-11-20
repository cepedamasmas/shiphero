# modules/kits_manager.py

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os
from modules.base import ShipHeroAPI
from utils.exceptions import ValidationError

class KitsManager(ShipHeroAPI):
    """
    Module for managing product kits in ShipHero.
    """
    
    def __init__(self):
        """Initialize the KitsManager module."""
        super().__init__()
        self.logger.info("KitsManager module initialized")

    def _build_kit_query(self, sku: str) -> str:
        """
        Build GraphQL query to get kit information.
        
        Args:
            sku (str): Kit SKU
            
        Returns:
            str: GraphQL query
        """
        return """
        query($sku: String!) {
            product(sku: $sku) {
                id
                sku
                name
                components {
                    id
                    sku
                    quantity
                    product {
                        name
                        sku
                    }
                }
            }
        }
        """

    def _build_kit_mutation(
        self,
        sku: str,
        components: List[Dict[str, Any]],
        warehouse_id: str,
        kit_build: bool = False
    ) -> str:
        """
        Build GraphQL mutation for creating/updating kits.
        
        Args:
            sku (str): Kit SKU
            components (List[Dict]): List of component details
            warehouse_id (str): Warehouse ID
            kit_build (bool): Whether to build the kit
            
        Returns:
            str: GraphQL mutation
        """
        return """
        mutation($sku: String!, $components: [KitComponentInput!]!, $warehouseId: ID!, $kitBuild: Boolean) {
            kit_build(
                data: {
                    sku: $sku
                    components: $components
                    warehouse_id: $warehouseId
                    kit_build: $kitBuild
                }
            ) {
                request_id
                complexity
                product {
                    id
                    sku
                    components {
                        id
                        sku
                    }
                }
            }
        }
        """

    def create_kit(
        self,
        kit_sku: str,
        components: List[Dict[str, Any]],
        warehouse_id: str,
        build_kit: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new kit with specified components.
        
        Args:
            kit_sku (str): SKU for the kit
            components (List[Dict]): List of component details
                Each component should have:
                - sku (str): Component SKU
                - quantity (int): Quantity needed
            warehouse_id (str): Warehouse ID
            build_kit (bool): Whether to build the kit immediately
            
        Returns:
            Dict[str, Any]: Created kit details
        """
        query = self._build_kit_mutation(kit_sku, components, warehouse_id, build_kit)
        
        variables = {
            "sku": kit_sku,
            "components": components,
            "warehouseId": warehouse_id,
            "kitBuild": build_kit
        }
        
        try:
            response = self._make_request(query, variables)
            self.logger.info(f"Kit {kit_sku} created successfully")
            return response['data']['kit_build']['product']
        except Exception as e:
            self.logger.error(f"Error creating kit {kit_sku}: {str(e)}")
            raise

    def remove_components(
        self,
        kit_sku: str,
        component_skus: List[str]
    ) -> Dict[str, Any]:
        """
        Remove components from an existing kit.
        
        Args:
            kit_sku (str): Kit SKU
            component_skus (List[str]): List of component SKUs to remove
            
        Returns:
            Dict[str, Any]: Updated kit details
        """
        query = """
        mutation($sku: String!, $components: [KitComponentInput!]!) {
            kit_remove_components(
                data: {
                    sku: $sku
                    components: $components
                }
            ) {
                request_id
                complexity
                product {
                    id
                    sku
                    components {
                        id
                        sku
                    }
                }
            }
        }
        """
        
        variables = {
            "sku": kit_sku,
            "components": [{"sku": sku} for sku in component_skus]
        }
        
        try:
            response = self._make_request(query, variables)
            self.logger.info(f"Components removed from kit {kit_sku}")
            return response['data']['kit_remove_components']['product']
        except Exception as e:
            self.logger.error(f"Error removing components from kit {kit_sku}: {str(e)}")
            raise

    def clear_kit(self, kit_sku: str) -> Dict[str, Any]:
        """
        Clear a kit (disassemble it) in all warehouses.
        
        Args:
            kit_sku (str): Kit SKU to clear
            
        Returns:
            Dict[str, Any]: Response details
        """
        query = """
        mutation($sku: String!) {
            kit_clear(data: { sku: $sku }) {
                request_id
                complexity
            }
        }
        """
        
        variables = {"sku": kit_sku}
        
        try:
            response = self._make_request(query, variables)
            self.logger.info(f"Kit {kit_sku} cleared successfully")
            return response['data']['kit_clear']
        except Exception as e:
            self.logger.error(f"Error clearing kit {kit_sku}: {str(e)}")
            raise

    def get_kit_details(self, kit_sku: str) -> pd.DataFrame:
        """
        Get detailed information about a kit and its components.
        
        Args:
            kit_sku (str): Kit SKU
            
        Returns:
            pd.DataFrame: Kit components details
        """
        query = self._build_kit_query(kit_sku)
        variables = {"sku": kit_sku}
        
        try:
            response = self._make_request(query, variables)
            product_data = response['data']['product']
            
            if not product_data:
                raise ValidationError(f"Kit {kit_sku} not found")
            
            components_data = []
            for component in product_data.get('components', []):
                component_detail = {
                    'kit_sku': kit_sku,
                    'kit_name': product_data.get('name'),
                    'component_sku': component.get('sku'),
                    'component_name': component.get('product', {}).get('name'),
                    'quantity': component.get('quantity'),
                    'component_id': component.get('id')
                }
                components_data.append(component_detail)
            
            return pd.DataFrame(components_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching kit details for {kit_sku}: {str(e)}")
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