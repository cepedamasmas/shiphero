import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class ShipHeroAPI:
    """
    Clase para interactuar con la API de ShipHero.
    """
    
    BASE_URL = "https://public-api.shiphero.com/graphql"
    
    def __init__(self, access_token: str, refresh_token: str, email: str):
        """
        Inicializa la clase con las credenciales necesarias.
        
        Args:
            access_token (str): Token de acceso JWT de ShipHero
            refresh_token (str): Token de actualización
            email (str): Email asociado a la cuenta
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.email = email
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Método interno para realizar peticiones GraphQL.
        
        Args:
            query (str): Query GraphQL
            variables (Dict, optional): Variables para la query
            
        Returns:
            Dict: Respuesta de la API
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = requests.post(
            self.BASE_URL,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 401:
            # Aquí se podría implementar la lógica de refresh token
            raise Exception("Token expirado o inválido")
            
        response.raise_for_status()
        return response.json()
