import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration OAuth et API
OAUTH_CONFIG = {
    'client_id': '49198',
    'api_key': os.getenv('BUNGIE_API_KEY'),
    'auth_url': 'https://www.bungie.net/en/OAuth/Authorize',
    'token_url': 'https://www.bungie.net/Platform/App/OAuth/token/',
    'redirect_uri': 'https://ory.ovh/'
}

# Composants Destiny 2
DESTINY_COMPONENTS = {
    'profiles': '100',
    'characters': '200',
    'characterEquipment': '205',
    'characterInventories': '201',
    'characterProgressions': '202',
    'characterActivities': '204',
    'itemInstances': '300',
    'currentActivities': '204'
}

# Types d'équipement
BUCKET_TYPES = {
    '1498876634': 'kinetic',
    '2465295065': 'energy',
    '953998645': 'power',
    '3448274439': 'helmet',
    '3551918588': 'gauntlets',
    '14239492': 'chest',
    '20886954': 'legs',
    '1585787867': 'class_item',
    '4023194814': 'ghost',
}

# Répertoires de l'application
DIRECTORIES = ['data', 'icons']

def create_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas."""
    for directory in DIRECTORIES:
        if not os.path.exists(directory):
            os.makedirs(directory)