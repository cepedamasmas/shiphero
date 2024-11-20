@echo off
echo Creando estructura de directorios para proyecto ShipHero...

:: Crear directorio raíz
mkdir shiphero
cd shiphero

:: Crear estructura de directorios
mkdir config
mkdir modules
mkdir utils
mkdir tests
mkdir logs
mkdir output

:: Crear archivos en config
echo. > config\.env
echo # Configuración general > config\config.py

:: Crear archivos en modules
echo. > modules\__init__.py
echo # Clase base ShipHero > modules\base.py
echo # Módulo de cambios de inventario > modules\inventory_changes.py
echo # Módulo de gestión de kits > modules\kits_manager.py
echo # Módulo de estado de inventario > modules\inventory_status.py

:: Crear archivos en utils
echo. > utils\__init__.py
echo # Configuración de logging > utils\logger.py
echo # Funciones auxiliares > utils\helpers.py
echo # Excepciones personalizadas > utils\exceptions.py

:: Crear archivos en tests
echo. > tests\__init__.py
echo # Tests de inventario > tests\test_inventory.py
echo # Tests de kits > tests\test_kits.py
echo # Tests de estado > tests\test_status.py

:: Crear archivos en logs y output
echo. > logs\.gitkeep
echo. > output\.gitkeep

:: Crear archivos en raíz
echo # ShipHero Integration > README.md
echo # Requirements > requirements.txt
echo # Main application > main.py

:: Crear .gitignore
echo .env > .gitignore
echo __pycache__/ >> .gitignore
echo *.pyc >> .gitignore
echo logs/* >> .gitignore
echo !logs/.gitkeep >> .gitignore
echo output/* >> .gitignore
echo !output/.gitkeep >> .gitignore
echo .pytest_cache/ >> .gitignore
echo .coverage >> .gitignore
echo .venv/ >> .gitignore

:: Crear virtual environment
python -m venv .venv

:: Mensaje final
echo.
echo Estructura de directorios creada exitosamente!
echo Para activar el entorno virtual:
echo .venv\Scripts\activate
echo.
echo Para instalar dependencias:
echo pip install -r requirements.txt
echo.

:: Crear requirements.txt con dependencias básicas
echo pandas>=1.5.0 > requirements.txt
echo requests>=2.28.0 >> requirements.txt
echo python-dotenv>=0.19.0 >> requirements.txt
echo pytest>=7.0.0 >> requirements.txt
echo black >> requirements.txt
echo flake8 >> requirements.txt
echo mypy >> requirements.txt
echo pytest-cov >> requirements.txt

pause
