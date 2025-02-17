import 'dart:convert';
import 'dart:typed_data';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

typedef OnImageReceived = void Function(Uint8List);

class MQTTService {
  final String broker = '150.140.186.118';
  final int port = 1883;
  late MqttServerClient client;
  final OnImageReceived onImageReceived;

  MQTTService({required this.onImageReceived});

  void connect() async {
    client = MqttServerClient(broker, 'flutter_client');
    client.port = port;
    client.logging(on: false);
    client.keepAlivePeriod = 60;
    
    final connMessage = MqttConnectMessage()
        .withClientIdentifier('flutter_client')
        .startClean()
        .withWillQos(MqttQos.atMostOnce);
    client.connectionMessage = connMessage;

    try {
      await client.connect();
      print("Connected to MQTT broker");
      subscribeToImageTopic();
    } catch (e) {
      print("Connection failed: $e");
    }
  }

  void subscribeToImageTopic() {
    client.subscribe("image", MqttQos.atMostOnce);
    client.updates!.listen((List<MqttReceivedMessage<MqttMessage?>>? messages) {
      final MqttPublishMessage recMessage = messages![0].payload as MqttPublishMessage;
      final String base64Image = MqttPublishPayload.bytesToStringAsString(recMessage.payload.message);
      onImageReceived(base64Decode(base64Image));
    });
  }
}
