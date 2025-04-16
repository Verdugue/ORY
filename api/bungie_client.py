import requests
import logging
from utils.config import OAUTH_CONFIG

class BungieClient:
    def __init__(self):
        self.api_key = OAUTH_CONFIG['api_key']
        
    def get_headers(self, access_token=None):
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        return headers
        
    def search_destiny_player(self, display_name, display_name_code):
        try:
            headers = self.get_headers()
            data = {
                'displayName': display_name,
                'displayNameCode': int(display_name_code)
            }
            
            response = requests.post(
                'https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayerByBungieName/-1/',
                headers=headers,
                json=data
            )
            
            return response.json() if response.status_code == 200 else None
            
        except Exception as e:
            logging.error(f"Erreur lors de la recherche du joueur: {str(e)}")
            return None