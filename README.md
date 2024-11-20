# Integración con ShipHero API

## Descripción General
Integración en Python con la API GraphQL de ShipHero para gestión de inventario, manejo de kits y seguimiento del estado del inventario.

## Instalación

1. Clonar el repositorio
2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```
3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Configuración

Crear un archivo `.env` en el directorio raíz con:

```env
SHIPHERO_ACCESS_TOKEN=tu_token_de_acceso
SHIPHERO_REFRESH_TOKEN=tu_token_de_refresco
SHIPHERO_EMAIL=tu_email
```

## Estructura del Proyecto
```
/shiphero/
  ├── config/          # Archivos de configuración
  ├── modules/         # Módulos principales
  ├── utils/           # Funciones auxiliares
  ├── tests/           # Suite de pruebas
  ├── logs/           # Archivos de registro
  └── output/         # Archivos CSV de salida
```

## Ejemplos de Uso

### Cambios de Inventario
```python
from modules.inventory_changes import InventoryChanges

# Inicializar módulo
inventario = InventoryChanges()

# Obtener cambios de los últimos 7 días
from datetime import datetime, timedelta
fecha_hasta = datetime.now().isoformat()
fecha_desde = (datetime.now() - timedelta(days=7)).isoformat()

# Obtener y exportar datos
df = inventario.get_inventory_changes(date_from=fecha_desde, date_to=fecha_hasta)
inventario.export_to_csv(df)
```

### Gestión de Kits
```python
from modules.kits_manager import KitsManager

# Inicializar módulo
kits = KitsManager()

# Crear un kit
componentes = [
    {"sku": "COMP1", "quantity": 2},
    {"sku": "COMP2", "quantity": 1}
]
kits.create_kit("KIT-SKU", componentes, "ID-ALMACEN")

# Obtener detalles del kit
df = kits.get_kit_details("KIT-SKU")
```

### Estado del Inventario
```python
from modules.inventory_status import InventoryStatus

# Inicializar módulo
estado = InventoryStatus()

# Obtener inventario actual
df = estado.get_inventory_status()

# Verificar items con stock bajo
stock_bajo = estado.get_low_stock_items(threshold=10)
```

## Ejecutar Pruebas

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar con cobertura
pytest --cov=modules tests/

# Ejecutar archivo específico de pruebas
pytest tests/test_inventory.py
```

## Documentación

Cada módulo incluye docstrings detallados en formato Google. Para más información:
```python
help(InventoryChanges)
help(KitsManager)
help(InventoryStatus)
```

## Manejo de Errores

La integración incluye un manejo completo de errores:
- Errores de autenticación
- Límite de tasa de consultas
- Errores de API
- Errores de validación

## Registro de Eventos (Logs)

Los logs se almacenan en el directorio `logs/` con rotación diaria y retención de 30 días.

## Características Principales

1. **Gestión de Inventario**
   - Seguimiento de cambios de inventario
   - Exportación a CSV con timestamp
   - Filtrado por fecha y SKU

2. **Gestión de Kits**
   - Creación y modificación de kits
   - Gestión de componentes
   - Consulta de detalles

3. **Estado de Inventario**
   - Consulta en tiempo real
   - Alertas de stock bajo
   - Seguimiento por almacén

4. **Características Técnicas**
   - Manejo automático de refresh token
   - Control de rate limiting
   - Sistema de caché
   - Logs detallados
   - Paginación automática

## Mantenimiento

1. **Logs**
   - Ubicación: directorio `logs/`
   - Rotación: diaria
   - Retención: 30 días

2. **Archivos de Salida**
   - Ubicación: directorio `output/`
   - Formato: CSV
   - Nomenclatura: `{tipo}_{timestamp}.csv`

3. **Caché**
   - TTL: 5 minutos
   - Almacenamiento: en memoria

## Contribuciones

1. Hacer fork del repositorio
2. Crear una rama para la funcionalidad
3. Comitear cambios (siguiendo Conventional Commits)
4. Enviar Pull Request

## Licencia

MIT License