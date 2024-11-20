# tests/test_kits.py

import pytest
import pandas as pd
from modules.kits_manager import KitsManager
from utils.exceptions import ValidationError

class TestKitsManager:
    @pytest.fixture
    def kits_module(self):
        return KitsManager()
    
    def test_build_kit_query(self, kits_module):
        """Test building kit query."""
        query = kits_module._build_kit_query("TEST-KIT")
        assert "product" in query
        assert "components" in query
        
    def test_build_kit_mutation(self, kits_module):
        """Test building kit mutation."""
        components = [{"sku": "COMP1", "quantity": 1}]
        query = kits_module._build_kit_mutation(
            "TEST-KIT",
            components,
            "WAREHOUSE1"
        )
        assert "kit_build" in query
        assert "components" in query
        
    @pytest.mark.vcr()
    def test_create_kit(self, kits_module):
        """Test kit creation."""
        components = [
            {"sku": "COMP1", "quantity": 2},
            {"sku": "COMP2", "quantity": 1}
        ]
        
        result = kits_module.create_kit(
            "TEST-KIT",
            components,
            "WAREHOUSE1"
        )
        
        assert result["sku"] == "TEST-KIT"
        assert len(result["components"]) == 2
        
    @pytest.mark.vcr()
    def test_get_kit_details(self, kits_module):
        """Test fetching kit details."""
        df = kits_module.get_kit_details("TEST-KIT")
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "kit_sku" in df.columns
        assert "component_sku" in df.columns
        assert "quantity" in df.columns