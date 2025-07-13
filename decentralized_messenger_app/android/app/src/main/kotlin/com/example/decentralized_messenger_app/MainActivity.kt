package com.example.decentralized_messenger_app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.EventChannel
import org.json.JSONObject
import java.io.File
import java.util.UUID
import java.util.Base64 // For Base64 encoding/decoding
import org.json.JSONArray // Explicitly import JSONArray

class MainActivity: FlutterActivity() {
    private val METHOD_CHANNEL_NAME = "com.example.decentralized_messenger/p2p_methods"
    private val EVENT_CHANNEL_NAME = "com.example.decentralized_messenger/p2p_events"

    private lateinit var methodChannel: MethodChannel
    private lateinit var eventChannel: EventChannel
    private var eventSink: EventChannel.EventSink? = null

    // Load the Rust library
    companion object {
        init {
            System.loadLibrary("decentralized_messenger_core")
        }
    }

    // Declare native functions from Rust
    private external fun generate_rsa_key_pair_ffi(): String
    private external fun encrypt_aes_key_with_rsa_ffi(aesKeyBase64: String, recipientPublicKeyPem: String): String
    private external fun decrypt_aes_key_with_rsa_ffi(encryptedAesKeyBase64: String, privateKeyPem: String): String
    private external fun generate_aes_key_ffi(): String
    private external fun encrypt_message_with_aes_ffi(message: String, aesKeyBase64: String): String
    private external fun decrypt_message_with_aes_ffi(ivBase64: String, ciphertextBase64: String, aesKeyBase64: String): String
    // private external fun free_cstring(ptr: String) // Not needed if Rust returns managed strings or JSON

    // --- Simulated User Data and P2P Storage ---
    private var currentUserId: String? = null
    private var myPublicKey: String? = null
    private var myPrivateKey: String? = null
    private val contacts = mutableMapOf<String, ContactInfo>() // contactId -> ContactInfo

    data class ContactInfo(
        val publicKey: String,
        val conversationPrivateKey: String, // Our private key for this conversation
        val conversationPublicKey: String   // Our public key for this conversation
    )

    // Simulated storage for user data and inboxes
    private fun getUserDataFile(): File {
        return File(applicationContext.filesDir, "user_data.json")
    }

    private fun getInboxFile(userId: String): File {
        return File(applicationContext.filesDir, "inbox_${userId}.json")
    }

    private fun saveUserData() {
        val userData = JSONObject().apply {
            put("userId", currentUserId)
            put("publicKey", myPublicKey)
            put("privateKey", myPrivateKey)
            val contactsJson = JSONObject()
            contacts.forEach { (id, info) ->
                contactsJson.put(id, JSONObject().apply {
                    put("publicKey", info.publicKey)
                    put("conversationPrivateKey", info.conversationPrivateKey)
                    put("conversationPublicKey", info.conversationPublicKey)
                })
            }
            put("contacts", contactsJson)
        }
        getUserDataFile().writeText(userData.toString())
    }

    private fun loadUserData() {
        val file = getUserDataFile()
        if (file.exists()) {
            val json = file.readText()
            val userData = JSONObject(json)
            currentUserId = userData.optString("userId")
            myPublicKey = userData.optString("publicKey")
            myPrivateKey = userData.optString("privateKey")
            val contactsJson = userData.optJSONObject("contacts")
            contactsJson?.keys()?.forEach { key ->
                val contactInfoJson = contactsJson.getJSONObject(key)
                contacts[key] = ContactInfo(
                    contactInfoJson.getString("publicKey"),
                    contactInfoJson.getString("conversationPrivateKey"),
                    contactInfoJson.getString("conversationPublicKey")
                )
            }
        }
    }

    // --- End Simulated User Data and P2P Storage ---


    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        loadUserData() // Load user data on startup

        methodChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, METHOD_CHANNEL_NAME)
        methodChannel.setMethodCallHandler { call, result ->
            when (call.method) {
                "initUser" -> {
                    if (currentUserId == null) {
                        // Create new user
                        val keyPairJson = generate_rsa_key_pair_ffi()
                        val keyPair = JSONObject(keyPairJson)
                        myPublicKey = keyPair.getString("public_key_pem")
                        myPrivateKey = keyPair.getString("private_key_pem")
                        currentUserId = UUID.randomUUID().toString().replace("-", "").substring(0, 100) // 100-char ID
                        saveUserData()
                    }
                    result.success(JSONObject().apply {
                        put("userId", currentUserId)
                        put("publicKey", myPublicKey)
                    }.toString())
                }
                "addContact" -> {
                    val contactId = call.argument<String>("contactId")
                    val contactPublicKey = call.argument<String>("contactPublicKey") // This would be exchanged in real P2P

                    if (contactId != null && contactPublicKey != null && !contacts.containsKey(contactId)) {
                        // Generate conversation-specific keys
                        val convKeyPairJson = generate_rsa_key_pair_ffi()
                        val convKeyPair = JSONObject(convKeyPairJson)
                        val convPrivateKey = convKeyPair.getString("private_key_pem")
                        val convPublicKey = convKeyPair.getString("public_key_pem")

                        contacts[contactId] = ContactInfo(contactPublicKey, convPrivateKey, convPublicKey)
                        saveUserData()
                        result.success("Contact $contactId added.")
                    } else {
                        result.error("ADD_CONTACT_ERROR", "Invalid contact ID or already exists.", null)
                    }
                }
                "sendMessage" -> {
                    val recipientId = call.argument<String>("recipientId")
                    val messageContent = call.argument<String>("messageContent")

                    if (recipientId == null || messageContent == null) {
                        result.error("SEND_ERROR", "Recipient ID or message content missing.", null)
                        return@setMethodCallHandler
                    }

                    val contactInfo = contacts[recipientId]
                    if (contactInfo == null) {
                        result.error("SEND_ERROR", "Contact not found. Add them first.", null)
                        return@setMethodCallHandler
                    }

                    try {
                        // 1. Generate AES key
                        val aesKeyBase64 = generate_aes_key_ffi()

                        // 2. Encrypt message with AES
                        val encryptedMessageJson = encrypt_message_with_aes_ffi(messageContent, aesKeyBase64)
                        val encryptedMessage = JSONObject(encryptedMessageJson)
                        val ivBase64 = encryptedMessage.getString("iv")
                        val ciphertextBase64 = encryptedMessage.getString("ciphertext")

                        // 3. Encrypt AES key with the recipient's public key (from contactInfo)
                        val encryptedAesKeyBase64 = encrypt_aes_key_with_rsa_ffi(aesKeyBase64, contactInfo.publicKey)

                        // 4. Construct message payload (simulated)
                        val messagePayload = JSONObject().apply {
                            put("senderId", currentUserId)
                            put("recipientId", recipientId)
                            put("encryptedAesKey", encryptedAesKeyBase64)
                            put("iv", ivBase64)
                            put("ciphertext", ciphertextBase64)
                            put("timestamp", System.currentTimeMillis())
                        }

                        // Simulate P2P send (write to recipient's inbox file)
                        val recipientInboxFile = getInboxFile(recipientId)
                        val messagesInInbox = if (recipientInboxFile.exists()) {
                            try {
                                JSONObject(recipientInboxFile.readText()).optJSONArray("messages") ?: JSONArray()
                            } catch (e: Exception) {
                                JSONArray() // Handle malformed JSON
                            }
                        } else {
                            JSONArray()
                        }
                        messagesInInbox.put(messagePayload)
                        JSONObject().apply { put("messages", messagesInInbox) }.write(recipientInboxFile)

                        result.success("Message sent (simulated P2P).")
                    } catch (e: Exception) {
                        result.error("ENCRYPTION_ERROR", "Failed to encrypt/send message: ${e.message}", e.toString())
                    }
                }
                else -> result.notImplemented()
            }
        }

        eventChannel = EventChannel(flutterEngine.dartExecutor.binaryMessenger, EVENT_CHANNEL_NAME)
        eventChannel.setStreamHandler(object : EventChannel.StreamHandler {
            override fun onListen(arguments: Any?, sink: EventChannel.EventSink) {
                eventSink = sink
                // Start a background task to check for incoming messages periodically
                // In a real app, this would be a listener for actual P2P connections
                Thread {
                    while (true) {
                        Thread.sleep(5000) // Check every 5 seconds
                        currentUserId?.let { userId ->
                            val inboxFile = getInboxFile(userId)
                            if (inboxFile.exists()) {
                                try {
                                    val inboxContent = JSONObject(inboxFile.readText())
                                    val messagesArray = inboxContent.optJSONArray("messages") ?: JSONArray()
                                    if (messagesArray.length() > 0) {
                                        val newMessages = mutableListOf<JSONObject>()
                                        for (i in 0 until messagesArray.length()) {
                                            newMessages.add(messagesArray.getJSONObject(i))
                                        }
                                        // Clear inbox after reading
                                        JSONObject().apply { put("messages", JSONArray()) }.write(inboxFile)

                                        newMessages.forEach { rawMessage ->
                                            try {
                                                val senderId = rawMessage.getString("senderId")
                                                val encryptedAesKeyBase64 = rawMessage.getString("encryptedAesKey")
                                                val ivBase64 = rawMessage.getString("iv")
                                                val ciphertextBase64 = rawMessage.getString("ciphertext")

                                                val contactInfo = contacts[senderId]
                                                if (contactInfo == null) {
                                                    eventSink?.error("DECRYPT_ERROR", "No contact info for $senderId. Cannot decrypt.", null)
                                                    return@forEach
                                                }

                                                // Decrypt AES key with our conversation-specific private key
                                                val decryptedAesKeyBase64 = decrypt_aes_key_with_rsa_ffi(encryptedAesKeyBase64, contactInfo.conversationPrivateKey)

                                                // Decrypt message content with AES key
                                                val decryptedMessage = decrypt_message_with_aes_ffi(ivBase64, ciphertextBase64, decryptedAesKeyBase64)

                                                eventSink?.success("From $senderId: $decryptedMessage")
                                            } catch (e: Exception) {
                                                eventSink?.error("DECRYPT_ERROR", "Failed to decrypt message: ${e.message}", rawMessage.toString())
                                            }
                                        }
                                    }
                                } catch (e: Exception) {
                                    // Handle JSON parsing errors for inbox file
                                    eventSink?.error("INBOX_READ_ERROR", "Failed to read inbox: ${e.message}", null)
                                }
                            }
                        }
                    }.start()
                }

                override fun onCancel(arguments: Any?) {
                    eventSink = null
                }
            })
        }
    }

    // Extension function to write JSONObject to file
    fun JSONObject.write(file: File) {
        file.writeText(this.toString())
    }
    