use rsa::{RsaPrivateKey, RsaPublicKey, pkcs1v15, traits::{PublicKeyParts, PrivateKeyParts}};
use rand::rngs::OsRng;
use serde::{Serialize, Deserialize};
use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use serde_json;
use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, NewAead};
use base64::{engine::general_purpose, Engine as _};
use rand_core::RngCore; // For generating random nonces

// Structs for serialization/deserialization
#[derive(Serialize, Deserialize, Debug)]
pub struct RsaKeyPair {
    pub private_key_pem: String,
    pub public_key_pem: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct EncryptedMessage {
    pub iv: String,
    pub ciphertext: String,
}

// Helper to convert Rust String to C-compatible char pointer
fn to_c_string(s: String) -> *mut c_char {
    CString::new(s).unwrap().into_raw()
}

// Helper to convert C-compatible char pointer to Rust String
fn from_c_string(ptr: *const c_char) -> String {
    unsafe {
        CStr::from_ptr(ptr).to_string_lossy().into_owned()
    }
}

// --- RSA Key Pair Generation ---
#[no_mangle]
pub extern "C" fn generate_rsa_key_pair_ffi() -> *mut c_char {
    let mut rng = OsRng;
    let bits = 2048;
    let private_key = RsaPrivateKey::new(&mut rng, bits).expect("failed to generate a key");
    let public_key = RsaPublicKey::from(&private_key);

    let private_key_pem = private_key.to_pkcs1_pem(pkcs1v15::LineEnding::LF).unwrap();
    let public_key_pem = public_key.to_pkcs1_pem(pkcs1v15::LineEnding::LF).unwrap();

    let key_pair = RsaKeyPair {
        private_key_pem,
        public_key_pem,
    };

    let json_string = serde_json::to_string(&key_pair).unwrap();
    to_c_string(json_string)
}

// --- Encrypt AES Key with RSA Public Key ---
#[no_mangle]
pub extern "C" fn encrypt_aes_key_with_rsa_ffi(
    aes_key_base64_ptr: *const c_char,
    recipient_public_key_pem_ptr: *const c_char,
) -> *mut c_char {
    let aes_key_base64 = from_c_string(aes_key_base64_ptr);
    let recipient_public_key_pem = from_c_string(recipient_public_key_pem_ptr);

    let aes_key_bytes = general_purpose::STANDARD.decode(aes_key_base64).unwrap();
    let recipient_public_key = RsaPublicKey::from_pkcs1_pem(&recipient_public_key_pem).unwrap();

    let encrypted_aes_key = recipient_public_key.encrypt(
        &mut OsRng,
        pkcs1v15::Oaep::new::<sha2::Sha256, sha2::Sha256>(),
        &aes_key_bytes,
    ).unwrap();

    to_c_string(general_purpose::STANDARD.encode(encrypted_aes_key))
}

// --- Decrypt AES Key with RSA Private Key ---
#[no_mangle]
pub extern "C" fn decrypt_aes_key_with_rsa_ffi(
    encrypted_aes_key_base64_ptr: *const c_char,
    private_key_pem_ptr: *const c_char,
) -> *mut c_char {
    let encrypted_aes_key_base64 = from_c_string(encrypted_aes_key_base64_ptr);
    let private_key_pem = from_c_string(private_key_pem_ptr);

    let encrypted_aes_key_bytes = general_purpose::STANDARD.decode(encrypted_aes_key_base64).unwrap();
    let private_key = RsaPrivateKey::from_pkcs1_pem(&private_key_pem).unwrap();

    let decrypted_aes_key = private_key.decrypt(
        &mut OsRng,
        pkcs1v15::Oaep::new::<sha2::Sha256, sha2::Sha256>(),
        &encrypted_aes_key_bytes,
    ).unwrap();

    to_c_string(general_purpose::STANDARD.encode(decrypted_aes_key))
}

// --- Generate AES Key ---
#[no_mangle]
pub extern "C" fn generate_aes_key_ffi() -> *mut c_char {
    let key = Aes256Gcm::generate_key(&mut OsRng);
    to_c_string(general_purpose::STANDARD.encode(key))
}

// --- Encrypt Message with AES ---
#[no_mangle]
pub extern "C" fn encrypt_message_with_aes_ffi(
    message_ptr: *const c_char,
    aes_key_base64_ptr: *const c_char,
) -> *mut c_char {
    let message = from_c_string(message_ptr);
    let aes_key_base64 = from_c_string(aes_key_base64_ptr);

    let key_bytes = general_purpose::STANDARD.decode(aes_key_base64).unwrap();
    let key = Key::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);

    let mut nonce_bytes = [0u8; 12]; // GCM nonces are typically 96 bits (12 bytes)
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);

    let ciphertext = cipher.encrypt(nonce, message.as_bytes()).unwrap();

    let encrypted_msg = EncryptedMessage {
        iv: general_purpose::STANDARD.encode(nonce),
        ciphertext: general_purpose::STANDARD.encode(ciphertext),
    };

    to_c_string(serde_json::to_string(&encrypted_msg).unwrap())
}

// --- Decrypt Message with AES ---
#[no_mangle]
pub extern "C" fn decrypt_message_with_aes_ffi(
    iv_base64_ptr: *const c_char,
    ciphertext_base64_ptr: *const c_char,
    aes_key_base64_ptr: *const c_char,
) -> *mut c_char {
    let iv_base64 = from_c_string(iv_base64_ptr);
    let ciphertext_base64 = from_c_string(ciphertext_base64_ptr);
    let aes_key_base64 = from_c_string(aes_key_base64_ptr);

    let key_bytes = general_purpose::STANDARD.decode(aes_key_base64).unwrap();
    let key = Key::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);

    let nonce_bytes = general_purpose::STANDARD.decode(iv_base64).unwrap();
    let nonce = Nonce::from_slice(&nonce_bytes);

    let ciphertext_bytes = general_purpose::STANDARD.decode(ciphertext_base64).unwrap();

    let decrypted_bytes = cipher.decrypt(nonce, ciphertext_bytes.as_slice()).unwrap();

    to_c_string(String::from_utf8(decrypted_bytes).unwrap())
}

// --- Free C-strings allocated by Rust ---
#[no_mangle]
pub extern "C" fn free_cstring(s: *mut c_char) {
    unsafe {
        if s.is_null() { return; }
        let _ = CString::from_raw(s);
    }
}
