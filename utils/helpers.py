# utils/helpers.py

from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, date
import hashlib
import json

def validate_date_format(date_str: str) -> bool:
    """
    Validate if a string is in ISO date format.
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def generate_cache_key(query: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a cache key from a GraphQL query and variables.
    
    Args:
        query (str): GraphQL query
        variables (Dict[str, Any], optional): Query variables
        
    Returns:
        str: Cache key
    """
    key_parts = [query]
    if variables:
        key_parts.append(json.dumps(variables, sort_keys=True))
    
    key_string = '|'.join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def prepare_mysql_upsert(
    df: pd.DataFrame,
    table_name: str,
    unique_columns: list
) -> tuple:
    """
    Prepare an upsert statement for MySQL.
    
    Args:
        df (pd.DataFrame): DataFrame containing the data
        table_name (str): Target table name
        unique_columns (list): Columns that form the unique constraint
        
    Returns:
        tuple: (sql_statement, values_list)
    """
    if df.empty:
        return None, None
        
    columns = list(df.columns)
    placeholders = ', '.join(['%s'] * len(columns))
    
    # Convert DataFrame to list of tuples for MySQL
    values = [tuple(x) for x in df.to_numpy()]
    
    # Build the INSERT statement
    insert_stmt = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    # Build the ON DUPLICATE KEY UPDATE part
    update_stmt = ", ".join([
        f"{col} = VALUES({col})"
        for col in columns
        if col not in unique_columns
    ])
    
    # Combine into upsert statement
    upsert_stmt = f"{insert_stmt} ON DUPLICATE KEY UPDATE {update_stmt}"
    
    return upsert_stmt, values

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize DataFrame columns.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # Convert column names to snake_case
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Convert datetime columns
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except:
                pass
    
    return df