
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class CryptoUtils:
    @staticmethod
    def generate_rsa_key_pair():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def serialize_public_key(public_key):
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    @staticmethod
    def deserialize_public_key(pem_data):
        return serialization.load_pem_public_key(
            pem_data.encode('utf-8'),
            backend=default_backend()
        )

    @staticmethod
    def serialize_private_key(private_key):
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

    @staticmethod
    def deserialize_private_key(pem_data):
        return serialization.load_pem_private_key(
            pem_data.encode('utf-8'),
            password=None,
            backend=default_backend()
        )

    @staticmethod
    def encrypt_aes_key_with_rsa(aes_key, recipient_public_key):
        encrypted_aes_key = recipient_public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_aes_key

    @staticmethod
    def decrypt_aes_key_with_rsa(encrypted_aes_key, private_key):
        decrypted_aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_aes_key

    @staticmethod
    def generate_aes_key():
        return os.urandom(32) # 256-bit key

    @staticmethod
    def encrypt_message_with_aes(message, aes_key):
        iv = os.urandom(16) # 128-bit IV
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        # PKCS7 padding
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(message.encode('utf-8')) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return iv, ciphertext

    @staticmethod
    def decrypt_message_with_aes(iv, ciphertext, aes_key):
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        # PKCS7 unpadding
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        message = unpadder.update(padded_data) + unpadder.finalize()
        return message.decode('utf-8')
