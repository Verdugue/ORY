import logging
import requests
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
from utils.config import OAUTH_CONFIG

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            query_components = parse_qs(urlparse(self.path).query)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            if 'code' in query_components:
                auth_code = query_components['code'][0]
                self.server.oauth_code = auth_code
                
                response_html = """
                <html>
                <body>
                    <h1>Authentification réussie!</h1>
                    <p>Vous pouvez fermer cette fenêtre et retourner à l'application.</p>
                    <script>window.close();</script>
                </body>
                </html>
                """
            else:
                response_html = """
                <html>
                <body>
                    <h1>Erreur d'authentification</h1>
                    <p>Code d'autorisation non trouvé.</p>
                </body>
                </html>
                """
            
            self.wfile.write(response_html.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Désactive les logs HTTP."""
        pass

class OAuthManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.oauth_server = None
        self.server_thread = None
    
    def save_tokens(self, token_data):
        try:
            with open('auth_tokens.json', 'w') as f:
                json.dump(token_data, f)
            logging.info("Tokens d'authentification sauvegardés")
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des tokens: {str(e)}")
            return False
    
    def load_tokens(self):
        try:
            if os.path.exists('auth_tokens.json'):
                with open('auth_tokens.json', 'r') as f:
                    token_data = json.load(f)
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                return True
        except Exception as e:
            logging.error(f"Erreur lors du chargement des tokens: {str(e)}")
        return False