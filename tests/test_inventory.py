# tests/test_inventory.py

import pytest
from datetime import datetime, timedelta
import pandas as pd
from modules.inventory_changes import InventoryChanges
from utils.exceptions import ValidationError

class TestInventoryChanges:
    @pytest.fixture
    def inventory_module(self):
        return InventoryChanges()
    
    def test_build_inventory_changes_query(self, inventory_module):
        """Test query building for inventory changes."""
        query = inventory_module._build_inventory_changes_query()
        assert "inventory_changes" in query
        assert "request_id" in query
        assert "edges" in query
        
    def test_flatten_inventory_change(self, inventory_module):
        """Test flattening of inventory change records."""
        test_node = {
            "user_id": "123",
            "account_id": "456",
            "warehouse_id": "789",
            "sku": "TEST-SKU",
            "previous_on_hand": 10,
            "change_in_on_hand": 5,
            "reason": "Receipt",
            "location": {
                "name": "Zone A",
                "zone": "A",
                "pickable": True
            }
        }
        
        flattened = inventory_module._flatten_inventory_change(test_node)
        assert flattened["sku"] == "TEST-SKU"
        assert flattened["current_on_hand"] == 15
        assert flattened["location_name"] == "Zone A"
        
    @pytest.mark.vcr()
    def test_get_inventory_changes(self, inventory_module):
        """Test fetching inventory changes."""
        date_from = (datetime.now() - timedelta(days=1)).isoformat()
        date_to = datetime.now().isoformat()
        
        df = inventory_module.get_inventory_changes(
            date_from=date_from,
            date_to=date_to,
            max_records=10
        )
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "sku" in df.columns
        assert "change_in_on_hand" in df.columns
        
    def test_export_to_csv(self, inventory_module, tmp_path):
        """Test CSV export functionality."""
        test_data = {
            "sku": ["TEST1", "TEST2"],
            "change_in_on_hand": [5, -3]
        }
        df = pd.DataFrame(test_data)
        
        filepath = inventory_module.export_to_csv(df)
        assert filepath.endswith(".csv")
        
        # Verify file contents
        exported_df = pd.read_csv(filepath)
        assert len(exported_df) == 2
        assert all(exported_df.columns == df.columns)