import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:convert'; // For JSON encoding/decoding

// Define the MethodChannel for communication with native platform code
const platformMethodChannel = MethodChannel('com.example.decentralized_messenger/p2p_methods');
// Define the EventChannel for receiving streams of data from native platform code
const platformEventChannel = EventChannel('com.example.decentralized_messenger/p2p_events');

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Decentralized Messenger',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const MessengerScreen(),
    );
  }
}

class MessengerScreen extends StatefulWidget {
  const MessengerScreen({super.key});

  @override
  State<MessengerScreen> createState() => _MessengerScreenState();
}

class _MessengerScreenState extends State<MessengerScreen> {
  final TextEditingController _recipientIdController = TextEditingController();
  final TextEditingController _messageController = TextEditingController();
  String _myPublicKey = 'Loading...';
  String _statusMessage = '';
  final List<String> _messages = [];

  @override
  void initState() {
    super.initState();
    _initMessenger();
    _listenForIncomingMessages();
  }

  Future<void> _initMessenger() async {
    try {
      // Call native method to initialize user or get existing ID/keys
      final String result = await platformMethodChannel.invokeMethod('initUser');
      final Map<String, dynamic> userData = jsonDecode(result);
      setState(() {
        _myPublicKey = userData['publicKey'] ?? 'Error getting public key';
        _statusMessage = 'Initialized with ID: ${userData['userId']}';
      });
    } on PlatformException catch (e) {
      setState(() {
        _statusMessage = "Failed to initialize: '${e.message}'.";
      });
    }
  }

  void _listenForIncomingMessages() {
    platformEventChannel.receiveBroadcastStream().listen((dynamic event) {
      setState(() {
        _messages.add('Received: $event');
      });
    }, onError: (dynamic error) {
      setState(() {
        _messages.add('Error receiving message: ${error.message}');
      });
    });
  }

  Future<void> _addContact() async {
    final String contactId = _recipientIdController.text;
    // In a real app, you'd get the contact's public key via some out-of-band method
    // For this prototype, we'll assume it's hardcoded or manually entered for testing.
    // For now, let's use a dummy public key or prompt the user.
    // This is where the initial key exchange would happen.
    // For simplicity, we'll just pass the contact ID for now, and assume the native side handles key exchange.
    try {
      final String result = await platformMethodChannel.invokeMethod('addContact', {
        'contactId': contactId,
        'contactPublicKey': 'DUMMY_PUBLIC_KEY_FOR_PROTOTYPE' // Replace with actual key input
      });
      setState(() {
        _statusMessage = result;
      });
    } on PlatformException catch (e) {
      setState(() {
        _statusMessage = "Failed to add contact: '${e.message}'.";
      });
    }
  }

  Future<void> _sendMessage() async {
    final String recipientId = _recipientIdController.text;
    final String messageContent = _messageController.text;

    if (recipientId.isEmpty || messageContent.isEmpty) {
      setState(() {
        _statusMessage = 'Recipient ID and message cannot be empty.';
      });
      return;
    }

    try {
      final String result = await platformMethodChannel.invokeMethod('sendMessage', {
        'recipientId': recipientId,
        'messageContent': messageContent,
      });
      setState(() {
        _statusMessage = result;
        _messages.add('Sent to $recipientId: $messageContent');
        _messageController.clear();
      });
    } on PlatformException catch (e) {
      setState(() {
        _statusMessage = "Failed to send message: '${e.message}'.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Decentralized Messenger'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('My Public Key: $_myPublicKey', style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 8),
            Text('Status: $_statusMessage', style: const TextStyle(fontSize: 14, color: Colors.grey)),
            const SizedBox(height: 16),
            TextField(
              controller: _recipientIdController,
              decoration: const InputDecoration(
                labelText: 'Recipient ID',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      labelText: 'Message',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _sendMessage,
                  child: const Text('Send'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ElevatedButton(
                  onPressed: _addContact,
                  child: const Text('Add Contact (Conceptual)'),
                ),
            const SizedBox(height: 16),
            const Text('Messages:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Expanded(
              child: ListView.builder(
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4.0),
                    child: Text(_messages[index]),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}