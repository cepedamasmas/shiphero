# tests/test_inventory_status.py

import pytest
import pandas as pd
from modules.inventory_status import InventoryStatus
from utils.exceptions import ValidationError

class TestInventoryStatus:
    @pytest.fixture
    def status_module(self):
        return InventoryStatus()
    
    def test_build_inventory_query(self, status_module):
        """Test building inventory query."""
        query = status_module._build_inventory_query()
        assert "inventory" in query
        assert "warehouse_products" in query
        
    def test_flatten_inventory_record(self, status_module):
        """Test flattening inventory records."""
        test_node = {
            "id": "123",
            "sku": "TEST-SKU",
            "product": {
                "name": "Test Product",
                "barcode": "123456789"
            },
            "warehouse_products": [{
                "warehouse_id": "WH1",
                "on_hand": 10,
                "available": 8,
                "warehouse": {
                    "name": "Main Warehouse"
                }
            }]
        }
        
        flattened = status_module._flatten_inventory_record(test_node)
        assert len(flattened) == 1
        assert flattened[0]["sku"] == "TEST-SKU"
        assert flattened[0]["on_hand"] == 10
        assert flattened[0]["warehouse_name"] == "Main Warehouse"
        
    @pytest.mark.vcr()
    def test_get_inventory_status(self, status_module):
        """Test fetching inventory status."""
        df = status_module.get_inventory_status(max_records=10)
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "sku" in df.columns
        assert "on_hand" in df.columns
        assert "available" in df.columns
        
    def test_get_low_stock_items(self, status_module):
        """Test low stock items detection."""
        df = status_module.get_low_stock_items(threshold=5)
        
        assert isinstance(df, pd.DataFrame)
        assert all(df['available'] <= 5)
        assert df.index.is_monotonic_increasing