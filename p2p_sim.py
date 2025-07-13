
import os
import json

INBOX_DIR = os.path.join(os.path.dirname(__file__), 'data', 'inboxes')

class P2PSimulator:
    @staticmethod
    def send_message(recipient_id, message_json):
        # In a real P2P network, this would involve discovering the recipient
        # and establishing a direct connection (Bluetooth, Wi-Fi Direct, etc.)
        # For simulation, we write to the recipient's inbox file.
        inbox_file = os.path.join(INBOX_DIR, f'{recipient_id}.json')
        
        messages = []
        if os.path.exists(inbox_file):
            with open(inbox_file, 'r') as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    messages = [] # Handle empty or malformed JSON
        
        messages.append(json.loads(message_json))
        
        with open(inbox_file, 'w') as f:
            json.dump(messages, f, indent=4)
        print(f"Simulated send: Message written to {recipient_id}'s inbox.")

    @staticmethod
    def receive_messages(my_id):
        # In a real P2P network, this would involve listening for incoming connections
        # and receiving data over the established channels.
        # For simulation, we read from our own inbox file.
        inbox_file = os.path.join(INBOX_DIR, f'{my_id}.json')
        
        if not os.path.exists(inbox_file):
            return []

        messages = []
        with open(inbox_file, 'r') as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                pass # No messages or malformed
        
        # Clear the inbox after reading
        if messages:
            with open(inbox_file, 'w') as f:
                json.dump([], f) # Clear the file
        
        return messages
