import requests
import json
from datetime import datetime, timedelta

class ShipHeroAPI:
    """
    Clase para interactuar con la API de ShipHero.
    """
    
    BASE_URL = "https://public-api.shiphero.com/graphql"
    
    def __init__(self, access_token: str, refresh_token: str, email: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.email = email
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def test_connection(self):
        """
        Test simple para verificar la conexión usando una consulta de inventory_changes
        """
        # Crear fechas para el rango de los últimos 7 días
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        query = """
        query {
          inventory_changes {
            request_id
            complexity
            data(first: 10) {
              edges {
                node {
                  user_id
                  account_id
                  warehouse_id
                  sku
                  previous_on_hand
                  change_in_on_hand
                  reason
                  cycle_counted
                  location_id
                  created_at
                }
              }
            }
          }
        }
        """
        
        try:
            response = requests.post(
                self.BASE_URL,
                headers=self.headers,
                json={"query": query}
            )
            
            # Si hay error, intentar obtener el mensaje detallado
            if response.status_code != 200:
                error_detail = response.json() if response.text else "No detail available"
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response body: {error_detail}")
                return False, error_detail
                
            data = response.json()
            return True, data
            
        except Exception as e:
            return False, str(e)

def run_test():
    """
    Función principal de prueba
    """
    # Credenciales
    ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlJUQXlOVU13T0Rrd09ETXhSVVZDUXpBNU5rSkVOVVUxUmtNeU1URTRNMEkzTWpnd05ERkdNdyJ9.eyJodHRwOi8vc2hpcGhlcm8tcHVibGljLWFwaS91c2VyaW5mbyI6eyJhY2NvdW50X2lkIjo2NDE1NSwiY2xpZW50X25hbWUiOiJTaGlwaGVybyBQdWJsaWMgQVBJIEdhdGV3YXkiLCJkYXRhIjp7fSwiaWQiOiJtdGNid3FJMnI2MTNEY09OM0RiVWFITHFRelE0ZGtobiIsIm5hbWUiOiJwZnN0ZWFybnNAZ21haWwuY29tIiwibmlja25hbWUiOiJwZnN0ZWFybnMiLCJwaWN0dXJlIjoiaHR0cHM6Ly9zLmdyYXZhdGFyLmNvbS9hdmF0YXIvMGUwZjQ0YWRlM2ZhMjA2N2QwYTAyOTEyODA0YjkzZWI_cz00ODAmcj1wZyZkPWh0dHBzJTNBJTJGJTJGY2RuLmF1dGgwLmNvbSUyRmF2YXRhcnMlMkZwZi5wbmcifSwiaXNzIjoiaHR0cHM6Ly9sb2dpbi5zaGlwaGVyby5jb20vIiwic3ViIjoiYXV0aDB8NDMxNjcyIiwiYXVkIjpbInNoaXBoZXJvLXB1YmxpYy1hcGkiLCJodHRwczovL3NoaXBoZXJvLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3MzE5NTQ2NzQsImV4cCI6MTczNDM3Mzg3NCwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSB2aWV3OnByb2R1Y3RzIGNoYW5nZTpwcm9kdWN0cyB2aWV3Om9yZGVycyBjaGFuZ2U6b3JkZXJzIHZpZXc6cHVyY2hhc2Vfb3JkZXJzIGNoYW5nZTpwdXJjaGFzZV9vcmRlcnMgdmlldzpzaGlwbWVudHMgY2hhbmdlOnNoaXBtZW50cyB2aWV3OnJldHVybnMgY2hhbmdlOnJldHVybnMgdmlldzp3YXJlaG91c2VfcHJvZHVjdHMgY2hhbmdlOndhcmVob3VzZV9wcm9kdWN0cyB2aWV3OnBpY2tpbmdfc3RhdHMgdmlldzpwYWNraW5nX3N0YXRzIG9mZmxpbmVfYWNjZXNzIiwiZ3R5IjoicGFzc3dvcmQiLCJhenAiOiJtdGNid3FJMnI2MTNEY09OM0RiVWFITHFRelE0ZGtobiJ9.m76LWt3h8RkyGG1tcp7-XaDFmZ6BB1jFxk2GM6NzUTMgXElURa3ZgIrAm7QyGoEnOm9l3pcdIKBlId9zTs0PhRiPQAYLSEjZmZ1fbCacmUor7zfzqcWUeSGhECIGOrYhK5pa-mrdDNigcHL2a6hh5U5Lx7pAB7PtWWxo5ZUhZU9eSJJFYI7MrlBYKMM8vFw1u0FVhtxWEB9pW7Z12-HZQf7I62jSQrYkI3Vn6QoMhy1CsEzV60nCRdj4z2lj_IOjE4ghf98c677Vf540OzUnqj4YP_mbHATRjsC64ZInLSXqe25uwk1A1zjPBmDlXEvGhkeI4NWOdv-HvR7jRCrHCw"
    REFRESH_TOKEN = "vBjI2mO49kVmiZQCVixcVILJcmV0K1VGuMzU3HkxQHAyX"
    EMAIL = "pfstearns@gmail.com"

    print("🔍 Iniciando test de conexión con ShipHero...")
    print("📅 Consultando cambios de inventario...")
    
    try:
        # Crear instancia de ShipHeroAPI
        api = ShipHeroAPI(ACCESS_TOKEN, REFRESH_TOKEN, EMAIL)
        
        # Ejecutar test de conexión
        success, result = api.test_connection()
        
        if success:
            print("✅ Conexión exitosa!")
            print("\n📦 Primeros cambios de inventario encontrados:")
            # Intentamos mostrar los datos de manera más legible
            if 'data' in result:
                inventory_changes = result['data']['inventory_changes']['data']['edges']
                for change in inventory_changes[:3]:  # Mostrar solo los primeros 3 cambios
                    node = change['node']
                    print(f"\nSKU: {node['sku']}")
                    print(f"Cambio: {node['change_in_on_hand']}")
                    print(f"Razón: {node['reason']}")
                    print(f"Fecha: {node['created_at']}")
        else:
            print("❌ Error en la conexión:")
            print(f"Detalles del error: {result}")
            
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    run_test()