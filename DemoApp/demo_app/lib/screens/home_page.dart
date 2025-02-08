import 'dart:typed_data';
import 'package:flutter/material.dart';

import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:location/location.dart';
import '../services/mqtt_service.dart';
import '../widgets/loading_overlay.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  _MapScreenState createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  Uint8List? overlayImage;
  bool showOverlay = true;
  bool isLoading = false;
  Location location = Location();
  LatLng userLocation = LatLng(37.7749, -122.4194);
  late MQTTService mqttService;

  @override
  void initState() {
    super.initState();
    mqttService = MQTTService(onImageReceived: (Uint8List image) {
      setState(() {
        isLoading = true;
      });
      Future.delayed(Duration(milliseconds: 500), () {
        setState(() {
          overlayImage = image;
          isLoading = false;
        });
      });
    });
    mqttService.connect();
    getUserLocation();
  }

  void getUserLocation() async {
    bool serviceEnabled;
    PermissionStatus permissionGranted;

    serviceEnabled = await location.serviceEnabled();
    if (!serviceEnabled) {
      serviceEnabled = await location.requestService();
      if (!serviceEnabled) return;
    }

    permissionGranted = await location.hasPermission();
    if (permissionGranted == PermissionStatus.denied) {
      permissionGranted = await location.requestPermission();
      if (permissionGranted != PermissionStatus.granted) return;
    }

    location.onLocationChanged.listen((LocationData currentLocation) {
      setState(() {
        userLocation = LatLng(currentLocation.latitude!, currentLocation.longitude!);
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Live Map with MQTT Image"),
        actions: [
          IconButton(
            icon: Icon(showOverlay ? Icons.visibility : Icons.visibility_off),
            onPressed: () {
              setState(() {
                showOverlay = !showOverlay;
              });
            },
          )
        ],
      ),
      body: Stack(
        children: [
          Positioned.fill(
            child: FlutterMap(
              options: MapOptions(
                initialCenter: userLocation,
                initialZoom: 15.0,
              ),
              children: [
                TileLayer(
                  urlTemplate: "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                  // subdomains: ['a', 'b', 'c'],
                ),
                // MarkerLayer(
                //   markers: [
                //     Marker(
                //       point: userLocation,
                //       builder: (ctx) => Icon(
                //         Icons.person_pin_circle,
                //         color: Colors.blue,
                //         size: 40.0,
                //       ),
                //     )
                //   ],
                // ),
                if (showOverlay && overlayImage != null)
                  OverlayImageLayer(
                    overlayImages: [
                      OverlayImage(
                        bounds: LatLngBounds(
                            LatLng(userLocation.latitude - 0.005, userLocation.longitude - 0.005),
                            LatLng(userLocation.latitude + 0.005, userLocation.longitude + 0.005)),
                        imageProvider: MemoryImage(overlayImage!),
                      )
                    ],
                  ),
              ],
            ),
          ),
          LoadingOverlay(isLoading: isLoading),
        ],
      ),
    );
  }
}
