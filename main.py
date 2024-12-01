# main.py

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
import time

from modules.inventory_changes import InventoryChanges
from modules.kits_manager import KitsManager
from modules.inventory_status import InventoryStatus
from modules.products import Products
from modules.warehouse import Warehouse
from modules.inventory_snapshot import InventorySnapshot
from utils.logger import setup_logger
from utils.helpers import validate_date_format
from config.config import Config

from utils.database import Database
from modules.models import SphVersion, SphInventarioDetalle, SphSnapshotInventario


logger = setup_logger("main")
db = Database()

def setup_argparse() -> argparse.ArgumentParser:
    """Configura los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='ShipHero Integration CLI')
    
    parser.add_argument(
        '--module',
        choices=['inventory', 'kits', 'status', 'products','account','snapshot'],
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
    
    parser.add_argument(
        '--snapshot-id',
        help='ID de inventory snapshot',
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

    if action == "load_database":
            
        logger.info(f"Obteniendo totalidad de inventario")
        
        df = inventory_module.get_inventory_changes(
            date_from=date_from,
            date_to=date_to,
            sku=sku,
            location_id=None,
            max_records=50000
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

def process_account(
    action: str,
    warehouse_id: Optional[str] = None
) -> None:
    """
    Procesa operaciones de products.
    
    Args:
        action (str): Acción a realizar
        sku (str, optional): SKU del kit
    """
    warehouse_module = Warehouse()
    
    if action == "get_warehouses":

        logger.info(f"Obteniendo detalles de la cuenta")
        df = warehouse_module.get_warehouses()
        return df
        
    elif action == "get_warehouse_products":
        # Si no se especifican fechas, usar últimos 7 días
        if not warehouse_id:
            logger.error(f"Necesita ingresar un warehouse id")
            sys.exit(1)
        logger.info(f"Obteniendo productos del warehouse {warehouse_id}")
        
        df = warehouse_module.get_warehouse_products(
            warehouse_id=warehouse_id,
            max_records=10
        )
        
        # Mostrar resumen
        print("\nResumen de productos del warehouse:")
        print(f"Total de registros: {len(df)}")
        print("\nMuestra de datos:")
        print(df.head())
        
        # Exportar a CSV
        csv_path = warehouse_module.export_to_csv(df)
        print(f"\nDatos exportados a: {csv_path}")
        
    else:
        logger.error(f"Acción no reconocida: {action}")
        sys.exit(1)

def process_snapshot(
    action: str,
    warehouse_id: Optional[str] = None,
    snapshot_id: Optional[str] = None
) -> None:
    """
    Procesa operaciones de products.
    
    Args:
        action (str): Acción a realizar
        sku (str, optional): SKU del kit
    """
    inventory_snapshot_module = InventorySnapshot()
    
    if action == "generate_snapshot":
        if not warehouse_id:
            logger.error(f"Necesita ingresar un warehouse id")
            sys.exit(1)
        logger.info(f"Generar snapshot del inventario del warehouse {warehouse_id}")
        snapshot_id = inventory_snapshot_module.generate_snapshot(warehouse_id=warehouse_id)
        return snapshot_id
    
    elif action == 'get_snapshot':
        
        if not snapshot_id:
            logger.error(f"Necesita ingresar un snapshot id")
            sys.exit(1)
        logger.info(f"Obteniendo detalles de snapshot")
        df = inventory_snapshot_module.get_snapshot_by_id(snapshot_id=snapshot_id)
        return df
    
    elif action == 'get_inventory':
        logger.info(f"Obtener todos los datos del inventario")

        df_warehouses = process_account('get_warehouses')
        
        # Insertar un registro
        with db.get_db() as session:
            sph_version_id = db.insert_record(
                db_session=session,
                model=SphVersion
            )
            print(f"Registro insertado con ID: {sph_version_id}")
        
        for index, row in df_warehouses.iterrows():
            snapshot_id = process_snapshot('generate_snapshot',row['warehouse_id'])
            snapshot_url = None
            max_intentos = 10
            intentos = 0

            while not snapshot_url and intentos < max_intentos:
                # Realiza las acciones necesarias dentro del ciclo
                print(f"intento nro {intentos}")
                time.sleep(2)
                df_snapshot = process_snapshot('get_snapshot',None, snapshot_id)
                snapshot_url = df_snapshot.at[0, "snapshot_url"]
                print('snapshot_url', snapshot_url)
                intentos += 1

            df_snapshot['sph_version_id'] = sph_version_id
            
            data = df_snapshot.iloc[0].to_dict()

            # Eliminar columnas no definidas en el modelo (opcional)
            valid_keys = {col.name for col in SphSnapshotInventario.__table__.columns}
            filtered_data = {key: value for key, value in data.items() if key in valid_keys}

            with db.get_db() as session:
                sph_snapshot_inventario_id = db.insert_record(
                    db_session=session,
                    model=SphSnapshotInventario,
                    **filtered_data
                )
            #inventory_snapshot_module.insert_df_to_db(df_snapshot,'sph_snapshot_inventario')

            logger.info(f"Consumo la url con el json")
            df_inventory = inventory_snapshot_module.get_inventory_snapshot_by_url(
                snapshot_url=snapshot_url
            )
            df_inventory['sph_snapshot_inventario_id'] = sph_snapshot_inventario_id
            #inventory_snapshot_module.export_to_csv(df_inventory,f'{row["address_name"]}_inventario')
            inventory_snapshot_module.insert_df_to_db(df_inventory,'sph_inventario_detalle')


        
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
        
        
        # Inicializar la base de datos
        db.init_db()
        
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
        elif args.module == "account":
            process_account(
                args.action,
                args.warehouse_id
            )
        elif args.module == "snapshot":
            process_snapshot(
                args.action,
                args.warehouse_id,
                args.snapshot_id
            )
        else:
            logger.error(f"Módulo no reconocido: {args.module}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()