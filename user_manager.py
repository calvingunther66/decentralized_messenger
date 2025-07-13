
import json
import os
import secrets
from decentralized_messenger.crypto_utils import CryptoUtils

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_DIR = os.path.join(DATA_DIR, 'users')

class UserManager:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.user_data = {}
        if user_id:
            self._load_user_data()

    def _get_user_file_path(self):
        return os.path.join(USERS_DIR, f'{self.user_id}.json')

    def _load_user_data(self):
        file_path = self._get_user_file_path()
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                self.user_data = json.load(f)
        else:
            print(f"User data file not found for {self.user_id}. Creating new.")
            self.create_new_user()

    def _save_user_data(self):
        file_path = self._get_user_file_path()
        with open(file_path, 'w') as f:
            json.dump(self.user_data, f, indent=4)

    def create_new_user(self):
        if not self.user_id:
            self.user_id = self._generate_random_id()
        
        private_key, public_key = CryptoUtils.generate_rsa_key_pair()
        self.user_data = {
            'user_id': self.user_id,
            'public_key': CryptoUtils.serialize_public_key(public_key),
            'private_key': CryptoUtils.serialize_private_key(private_key),
            'contacts': {} # Stores public keys and conversation-specific private keys of contacts
        }
        self._save_user_data()
        print(f"New user created with ID: {self.user_id}")
        return self.user_id

    def _generate_random_id(self):
        return secrets.token_hex(50) # 100 character hex string

    def get_public_key(self):
        return self.user_data.get('public_key')

    def get_private_key(self):
        return CryptoUtils.deserialize_private_key(self.user_data.get('private_key'))

    def add_contact(self, contact_id, contact_public_key_pem):
        if contact_id not in self.user_data['contacts']:
            # Generate a new RSA key pair for this specific conversation
            private_key_conv, public_key_conv = CryptoUtils.generate_rsa_key_pair()
            self.user_data['contacts'][contact_id] = {
                'public_key': contact_public_key_pem, # Contact's main public key
                'conversation_private_key': CryptoUtils.serialize_private_key(private_key_conv),
                'conversation_public_key': CryptoUtils.serialize_public_key(public_key_conv) # Our public key for this conversation
            }
            self._save_user_data()
            print(f"Added contact {contact_id} and generated conversation keys.")
        else:
            print(f"Contact {contact_id} already exists.")

    def get_contact_public_key(self, contact_id):
        contact_data = self.user_data['contacts'].get(contact_id)
        if contact_data:
            return CryptoUtils.deserialize_public_key(contact_data['public_key'])
        return None

    def get_conversation_private_key(self, contact_id):
        contact_data = self.user_data['contacts'].get(contact_id)
        if contact_data:
            return CryptoUtils.deserialize_private_key(contact_data['conversation_private_key'])
        return None

    def get_conversation_public_key(self, contact_id):
        contact_data = self.user_data['contacts'].get(contact_id)
        if contact_data:
            return CryptoUtils.deserialize_public_key(contact_data['conversation_public_key'])
        return None

    def get_all_contacts(self):
        return list(self.user_data['contacts'].keys())
