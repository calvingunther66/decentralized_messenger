import 'dart:ffi';
import 'dart:io';
import 'package:ffi/ffi.dart';
import 'dart:convert';

// Define the Rust library path based on the operating system
final DynamicLibrary _rustLib = Platform.isWindows
    ? DynamicLibrary.open('decentralized_messenger_core.dll')
    : Platform.isMacOS
        ? DynamicLibrary.open('libdecentralized_messenger_core.dylib')
        : DynamicLibrary.open('libdecentralized_messenger_core.so');

// Define the C function signatures
typedef _GenerateRsaKeyPairC = Pointer<Utf8> Function();
typedef _EncryptAesKeyWithRsaC = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _DecryptAesKeyWithRsaC = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _GenerateAesKeyC = Pointer<Utf8> Function();
typedef _EncryptMessageWithAesC = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _DecryptMessageWithAesC = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>, Pointer<Utf8>);
typedef _FreeCStringC = Void Function(Pointer<Utf8>);

// Define the Dart function types
typedef _GenerateRsaKeyPairDart = Pointer<Utf8> Function();
typedef _EncryptAesKeyWithRsaDart = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _DecryptAesKeyWithRsaDart = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _GenerateAesKeyDart = Pointer<Utf8> Function();
typedef _EncryptMessageWithAesDart = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _DecryptMessageWithAesDart = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>, Pointer<Utf8>);
typedef _FreeCStringDart = void Function(Pointer<Utf8>);

// Look up the functions in the shared library
final _generateRsaKeyPair = _rustLib.lookupFunction<_GenerateRsaKeyPairC, _GenerateRsaKeyPairDart>('generate_rsa_key_pair_ffi');
final _encryptAesKeyWithRsa = _rustLib.lookupFunction<_EncryptAesKeyWithRsaC, _EncryptAesKeyWithRsaDart>('encrypt_aes_key_with_rsa_ffi');
final _decryptAesKeyWithRsa = _rustLib.lookupFunction<_DecryptAesKeyWithRsaC, _DecryptAesKeyWithRsaDart>('decrypt_aes_key_with_rsa_ffi');
final _generateAesKey = _rustLib.lookupFunction<_GenerateAesKeyC, _GenerateAesKeyDart>('generate_aes_key_ffi');
final _encryptMessageWithAes = _rustLib.lookupFunction<_EncryptMessageWithAesC, _EncryptMessageWithAesDart>('encrypt_message_with_aes_ffi');
final _decryptMessageWithAes = _rustLib.lookupFunction<_DecryptMessageWithAesC, _DecryptMessageWithAesDart>('decrypt_message_with_aes_ffi');
final _freeCString = _rustLib.lookupFunction<_FreeCStringC, _FreeCStringDart>('free_cstring');

// Wrapper functions for easier Dart usage
class RustCore {
  static Map<String, String> generateRsaKeyPair() {
    final ptr = _generateRsaKeyPair();
    final jsonString = ptr.toDartString();
    _freeCString(ptr); // Free the CString
    return Map<String, String>.from(jsonDecode(jsonString));
  }

  static String encryptAesKeyWithRsa(String aesKeyBase64, String recipientPublicKeyPem) {
    final ptr = _encryptAesKeyWithRsa(aesKeyBase64.toNativeUtf8(), recipientPublicKeyPem.toNativeUtf8());
    final result = ptr.toDartString();
    _freeCString(ptr);
    return result;
  }

  static String decryptAesKeyWithRsa(String encryptedAesKeyBase64, String privateKeyPem) {
    final ptr = _decryptAesKeyWithRsa(encryptedAesKeyBase64.toNativeUtf8(), privateKeyPem.toNativeUtf8());
    final result = ptr.toDartString();
    _freeCString(ptr);
    return result;
  }

  static String generateAesKey() {
    final ptr = _generateAesKey();
    final result = ptr.toDartString();
    _freeCString(ptr);
    return result;
  }

  static Map<String, String> encryptMessageWithAes(String message, String aesKeyBase64) {
    final ptr = _encryptMessageWithAes(message.toNativeUtf8(), aesKeyBase64.toNativeUtf8());
    final jsonString = ptr.toDartString();
    _freeCString(ptr);
    return Map<String, String>.from(jsonDecode(jsonString));
  }

  static String decryptMessageWithAes(String ivBase64, String ciphertextBase64, String aesKeyBase64) {
    final ptr = _decryptMessageWithAes(ivBase64.toNativeUtf8(), ciphertextBase64.toNativeUtf8(), aesKeyBase64.toNativeUtf8());
    final result = ptr.toDartString();
    _freeCString(ptr);
    return result;
  }
}
