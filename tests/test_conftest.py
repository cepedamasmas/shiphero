# tests/conftest.py

import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def env_setup():
    """Set up test environment variables."""
    load_dotenv()
    
    # Set up test environment variables if not present
    if not os.getenv("SHIPHERO_ACCESS_TOKEN"):
        os.environ["SHIPHERO_ACCESS_TOKEN"] = "test_access_token"
    if not os.getenv("SHIPHERO_REFRESH_TOKEN"):
        os.environ["SHIPHERO_REFRESH_TOKEN"] = "test_refresh_token"
    if not os.getenv("SHIPHERO_EMAIL"):
        os.environ["SHIPHERO_EMAIL"] = "test@example.com"

@pytest.fixture
def sample_inventory_change():
    """Sample inventory change data."""
    return {
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

@pytest.fixture
def sample_kit():
    """Sample kit data."""
    return {
        "sku": "TEST-KIT",
        "components": [
            {"sku": "COMP1", "quantity": 2},
            {"sku": "COMP2", "quantity": 1}
        ]
    }

@pytest.fixture
def sample_inventory_status():
    """Sample inventory status data."""
    return {
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