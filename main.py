

import os
import json
from decentralized_messenger.user_manager import UserManager
from decentralized_messenger.crypto_utils import CryptoUtils
from decentralized_messenger.message_protocol import MessageProtocol
from decentralized_messenger.p2p_sim import P2PSimulator
from decentralized_messenger.location_manager import LocationManager

class DecentralizedMessenger:
    def __init__(self):
        self.user_manager = None
        self.current_user_id = None

    def _load_or_create_user(self):
        user_id_input = input("Enter your user ID (or leave blank to create a new one): ").strip()
        if user_id_input:
            self.current_user_id = user_id_input
            self.user_manager = UserManager(user_id=self.current_user_id)
            if not os.path.exists(os.path.join(self.user_manager.USERS_DIR, f'{self.current_user_id}.json')):
                print(f"User ID '{self.current_user_id}' not found. Creating new user with this ID.")
                self.user_manager.create_new_user()
        else:
            self.user_manager = UserManager()
            self.current_user_id = self.user_manager.create_new_user()
        print(f"Current User ID: {self.current_user_id}")

    def _add_contact(self):
        contact_id = input("Enter contact's 100-char ID: ").strip()
        contact_public_key_pem = input("Enter contact's public key (PEM format): ").strip()
        if contact_id and contact_public_key_pem:
            self.user_manager.add_contact(contact_id, contact_public_key_pem)
        else:
            print("Invalid input for contact ID or public key.")

    def _send_message(self):
        recipient_id = input("Enter recipient's 100-char ID: ").strip()
        message_content = input("Enter your message: ").strip()

        if not recipient_id or not message_content:
            print("Recipient ID and message content cannot be empty.")
            return

        # Ensure we have conversation keys for this recipient
        if recipient_id not in self.user_manager.get_all_contacts():
            print(f"You need to add {recipient_id} as a contact first to exchange public keys.")
            # In a real scenario, this would involve an initial handshake to exchange public keys
            # For now, we'll ask the user to manually add the contact's public key.
            return

        recipient_public_key = self.user_manager.get_contact_public_key(recipient_id)
        if not recipient_public_key:
            print(f"Could not retrieve public key for {recipient_id}. Make sure they are added as a contact.")
            return

        # Generate a new AES key for this message
        aes_key = CryptoUtils.generate_aes_key()

        # Encrypt the message with AES
        iv, ciphertext = CryptoUtils.encrypt_message_with_aes(message_content, aes_key)

        # Encrypt the AES key with the recipient's RSA public key (conversation-specific)
        encrypted_aes_key = CryptoUtils.encrypt_aes_key_with_rsa(aes_key, recipient_public_key)

        # Create the message protocol object
        message_json = MessageProtocol.create_message(
            self.current_user_id,
            recipient_id,
            encrypted_aes_key,
            iv,
            ciphertext
        )

        # Simulate sending the message
        P2PSimulator.send_message(recipient_id, message_json)
        print("Message sent (simulated).")

    def _receive_messages(self):
        print("Checking for new messages...")
        received_messages_raw = P2PSimulator.receive_messages(self.current_user_id)

        if not received_messages_raw:
            print("No new messages.")
            return

        for raw_msg in received_messages_raw:
            try:
                # Convert dict back to JSON string for parsing by MessageProtocol
                message_json_str = json.dumps(raw_msg)
                parsed_message = MessageProtocol.parse_message(message_json_str)

                sender_id = parsed_message['sender_id']
                encrypted_aes_key = parsed_message['encrypted_aes_key']
                iv = parsed_message['iv']
                ciphertext = parsed_message['ciphertext']

                # Get our conversation-specific private key for this sender
                conversation_private_key = self.user_manager.get_conversation_private_key(sender_id)
                if not conversation_private_key:
                    print(f"Warning: No conversation private key found for {sender_id}. Cannot decrypt message.")
                    continue

                # Decrypt the AES key with our conversation-specific RSA private key
                decrypted_aes_key = CryptoUtils.decrypt_aes_key_with_rsa(encrypted_aes_key, conversation_private_key)

                # Decrypt the message content with the AES key
                decrypted_message = CryptoUtils.decrypt_message_with_aes(iv, ciphertext, decrypted_aes_key)

                print(f"\n--- New Message from {sender_id} ({parsed_message['timestamp']}) ---")
                print(f"Message: {decrypted_message}")
                print("--------------------------------------")

            except Exception as e:
                print(f"Error processing message: {e}")
                print(f"Raw message: {raw_msg}")

    def _display_my_public_key(self):
        if self.user_manager:
            print("\nYour Public Key (share with others to receive messages):\n")
            print(self.user_manager.get_public_key())
            print("\n")
        else:
            print("Please load or create a user first.")

    def _display_contacts(self):
        if self.user_manager:
            contacts = self.user_manager.get_all_contacts()
            if contacts:
                print("\nYour Contacts:")
                for contact in contacts:
                    print(f"- {contact}")
                print("\n")
            else:
                print("You have no contacts yet.")
        else:
            print("Please load or create a user first.")

    def run(self):
        self._load_or_create_user()

        while True:
            print("\n--- Decentralized Messenger Menu ---")
            print("1. Send Message")
            print("2. Receive Messages")
            print("3. Add Contact")
            print("4. Display My Public Key")
            print("5. Display My Contacts")
            print("6. Exit")
            choice = input("Enter your choice: ").strip()

            if choice == '1':
                self._send_message()
            elif choice == '2':
                self._receive_messages()
            elif choice == '3':
                self._add_contact()
            elif choice == '4':
                self._display_my_public_key()
            elif choice == '5':
                self._display_contacts()
            elif choice == '6':
                print("Exiting messenger. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    messenger = DecentralizedMessenger()
    messenger.run()
