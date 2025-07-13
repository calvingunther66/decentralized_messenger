
import json
import base64
from datetime import datetime

class MessageProtocol:
    @staticmethod
    def create_message(sender_id, recipient_id, encrypted_aes_key, iv, ciphertext):
        message = {
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'encrypted_aes_key': base64.b64encode(encrypted_aes_key).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'timestamp': json.dumps(datetime.now().isoformat()) # Add timestamp
        }
        return json.dumps(message)

    @staticmethod
    def parse_message(json_message):
        message = json.loads(json_message)
        return {
            'sender_id': message['sender_id'],
            'recipient_id': message['recipient_id'],
            'encrypted_aes_key': base64.b64decode(message['encrypted_aes_key']),
            'iv': base64.b64decode(message['iv']),
            'ciphertext': base64.b64decode(message['ciphertext']),
            'timestamp': json.loads(message['timestamp'])
        }
