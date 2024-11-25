# main.py

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional

from modules.inventory_changes import InventoryChanges
from modules.kits_manager import KitsManager
from modules.inventory_status import InventoryStatus
from modules.products import Products
from utils.logger import setup_logger
from utils.helpers import validate_date_format
from config.config import Config

logger = setup_logger("main")

def setup_argparse() -> argparse.ArgumentParser:
    """Configura los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='ShipHero Integration CLI')
    
    parser.add_argument(
        '--module',
        choices=['inventory', 'kits', 'status', 'products'],
        help='Módulo a ejecutar (inventory, kits, status, products)',
        required=True
    )
    
    parser.add_argument(
        '--action',
        help='Acción a realizar dentro del módulo',
        required=True
    )
    
    parser.add_argument(
        '--date-from',
        help='Fecha inicio (YYYY-MM-DD)',
        required=False
    )
    
    parser.add_argument(
        '--date-to',
        help='Fecha fin (YYYY-MM-DD)',
        required=False
    )
    
    parser.add_argument(
        '--sku',
        help='SKU específico',
        required=False
    )
    
    parser.add_argument(
        '--warehouse-id',
        help='ID del almacén',
        required=False
    )
    
    return parser

def process_inventory_changes(
    action: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sku: Optional[str] = None
) -> None:
    """
    Procesa los cambios de inventario.
    
    Args:
        action (str): Acción a realizar
        date_from (str, optional): Fecha inicio
        date_to (str, optional): Fecha fin
        sku (str, optional): SKU específico
    """
    inventory_module = InventoryChanges()
    
    if action == "get_changes":
        # Si no se especifican fechas, usar últimos 7 días
        if not date_from:
            date_from = (datetime.now() - timedelta(days=7)).isoformat()
        if not date_to:
            date_to = datetime.now().isoformat()
            
        logger.info(f"Obteniendo cambios de inventario desde {date_from} hasta {date_to}")
        
        df = inventory_module.get_inventory_changes(
            date_from=date_from,
            date_to=date_to,
            sku=sku
        )
        
        # Mostrar resumen
        print("\nResumen de cambios de inventario:")
        print(f"Total de registros: {len(df)}")
        print("\nMuestra de datos:")
        print(df.head())
        
        # Exportar a CSV
        csv_path = inventory_module.export_to_csv(df)
        print(f"\nDatos exportados a: {csv_path}")
    else:
        logger.error(f"Acción no reconocida: {action}")
        sys.exit(1)

def process_kits(
    action: str,
    sku: Optional[str] = None,
    warehouse_id: Optional[str] = None
) -> None:
    """
    Procesa operaciones de kits.
    
    Args:
        action (str): Acción a realizar
        sku (str, optional): SKU del kit
        warehouse_id (str, optional): ID del almacén
    """
    kits_module = KitsManager()
    
    if action == "get_details":
        if not sku:
            logger.error("Se requiere SKU para obtener detalles del kit")
            sys.exit(1)
            
        logger.info(f"Obteniendo detalles del kit: {sku}")
        df = kits_module.get_kit_details(sku)
        
        print("\nDetalles del kit:")
        print(df)
        
        csv_path = kits_module.export_kit_details(df)
        print(f"\nDetalles exportados a: {csv_path}")
        
    elif action == "clear_kit":
        if not sku:
            logger.error("Se requiere SKU para limpiar el kit")
            sys.exit(1)
            
        logger.info(f"Limpiando kit: {sku}")
        result = kits_module.clear_kit(sku)
        print(f"Kit {sku} limpiado exitosamente")
        
    else:
        logger.error(f"Acción no reconocida: {action}")
        sys.exit(1)

def process_products(
    action: str,
    sku: Optional[str] = None
) -> None:
    """
    Procesa operaciones de products.
    
    Args:
        action (str): Acción a realizar
        sku (str, optional): SKU del kit
    """
    products_module = Products()
    
    if action == "get_details":

        logger.info(f"Obteniendo detalles de productos")
        df = products_module.get_products_details(sku)
        
        print("\nDetalles del kit:")
        print(df)
        
        #csv_path = products_module.export_kit_details(df)
        print(f"\nDetalles exportados a: {csv_path}")
        
    elif action == "clear_kit":
        if not sku:
            logger.error("Se requiere SKU para limpiar el kit")
            sys.exit(1)
            
        logger.info(f"Limpiando kit: {sku}")
        result = products_module.clear_kit(sku)
        print(f"Kit {sku} limpiado exitosamente")
        
    else:
        logger.error(f"Acción no reconocida: {action}")
        sys.exit(1)

def process_inventory_status(
    action: str,
    sku: Optional[str] = None,
    warehouse_id: Optional[str] = None
) -> None:
    """
    Procesa el estado del inventario.
    
    Args:
        action (str): Acción a realizar
        sku (str, optional): SKU específico
        warehouse_id (str, optional): ID del almacén
    """
    status_module = InventoryStatus()
    
    if action == "get_status":
        logger.info("Obteniendo estado del inventario")
        df = status_module.get_inventory_status(sku=sku)
        
        print("\nEstado actual del inventario:")
        print(f"Total de productos: {len(df)}")
        print("\nMuestra de datos:")
        print(df.head())
        
        csv_path = status_module.export_inventory_status(df)
        print(f"\nEstado exportado a: {csv_path}")
        
    elif action == "low_stock":
        logger.info("Verificando productos con stock bajo")
        df = status_module.get_low_stock_items(threshold=10)
        
        print("\nProductos con stock bajo:")
        print(df)
        
        if not df.empty:
            csv_path = status_module.export_inventory_status(
                df,
                prefix="low_stock"
            )
            print(f"\nReporte exportado a: {csv_path}")
    else:
        logger.error(f"Acción no reconocida: {action}")
        sys.exit(1)

def main():
    """Función principal de ejecución."""
    try:
        # Verificar configuración
        Config.validate_config()
        
        # Configurar argumentos
        parser = setup_argparse()
        args = parser.parse_args()
        
        # Validar fechas si se proporcionan
        if args.date_from and not validate_date_format(args.date_from):
            logger.error(f"Formato de fecha inválido: {args.date_from}")
            sys.exit(1)
        if args.date_to and not validate_date_format(args.date_to):
            logger.error(f"Formato de fecha inválido: {args.date_to}")
            sys.exit(1)
        
        # Procesar según el módulo seleccionado
        if args.module == "inventory":
            process_inventory_changes(
                args.action,
                args.date_from,
                args.date_to,
                args.sku
            )
        elif args.module == "kits":
            process_kits(
                args.action,
                args.sku,
                args.warehouse_id
            )
        elif args.module == "status":
            process_inventory_status(
                args.action,
                args.sku,
                args.warehouse_id
            )
        elif args.module == "products":
            process_products(
                args.action,
                args.sku
            )
        else:
            logger.error(f"Módulo no reconocido: {args.module}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()