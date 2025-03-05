import mysql.connector
import requests
import json
from typing import Dict
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def refresh_bungie_token() -> None:
    try:
        # Connexion à la base de données
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Récupérer les informations depuis la base de données
        cursor.execute("SELECT * FROM identification WHERE id = 1")
        result = cursor.fetchone()

        if not result:
            raise Exception("Aucune donnée d'identification trouvée")

        client_id = result['client']
        client_secret = result['client_secret']
        refresh_token = result['refresh']

        # URL du token Bungie
        token_url = "https://www.bungie.net/platform/app/oauth/token/"

        # Données pour la requête de rafraîchissement
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }

        # Headers pour la requête
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        # Effectuer la requête POST
        response = requests.post(
            token_url,
            data=data,
            headers=headers,
            verify=False  # Équivalent de CURLOPT_SSL_VERIFY
        )

        # Vérifier et traiter la réponse
        response_data = response.json()

        if 'access_token' in response_data:
            print(f"Nouveau Access Token : {response_data['access_token']}")
            print(f"Nouveau Refresh Token : {response_data['refresh_token']}")
            print(f"Expiration dans : {response_data['expires_in']} secondes.")

            # Sauvegarder dans un fichier JSON
            with open("bungie_tokens.json", "w") as f:
                json.dump(response_data, f, indent=4)

            # Mettre à jour la base de données
            update_query = """
                UPDATE identification 
                SET access = %s, refresh = %s 
                WHERE id = 1
            """
            cursor.execute(update_query, (
                response_data['access_token'],
                response_data['refresh_token']
            ))
            conn.commit()

        else:
            print("Erreur lors de la récupération du nouveau token :")
            print(json.dumps(response_data, indent=4))

    except mysql.connector.Error as db_error:
        print(f"Erreur avec la base de données : {db_error}")
    except requests.exceptions.RequestException as req_error:
        print(f"Erreur lors de la requête HTTP : {req_error}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    refresh_bungie_token() 