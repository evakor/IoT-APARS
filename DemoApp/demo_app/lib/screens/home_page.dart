import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:location/location.dart';
import '../services/mqtt_service.dart';
import '../widgets/loading_overlay.dart';

class MapScreen extends StatefulWidget {
  @override
  _MapScreenState createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  Uint8List? overlayImage;
  bool showOverlay = true;
  bool isLoading = false;
  bool isDarkMode = false;
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
    return MaterialApp(
      theme: isDarkMode ? ThemeData.dark() : ThemeData.light(),
      home: Scaffold(
        appBar: AppBar(
          title: Text("Home Page"),
          backgroundColor: Colors.blueAccent,
          leading: Builder(
            builder: (context) => IconButton(
              icon: Icon(Icons.menu),
              onPressed: () => Scaffold.of(context).openDrawer(),
            ),
          ),
        ),
        drawer: Drawer(
          child: ListView(
            padding: EdgeInsets.zero,
            children: <Widget>[
              DrawerHeader(
                decoration: BoxDecoration(
                  color: Colors.blueAccent,
                ),
                child: Text(
                  'Menu',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                  ),
                ),
              ),
              ListTile(
                leading: Icon(Icons.info),
                title: Text("About Us"),
                onTap: () {
                  print("Navigating to About Us...");
                },
              ),
              ListTile(
                leading: Icon(Icons.wifi),
                title: Text("Connect to APARS"),
                onTap: () {
                  print("Connecting to APARS...");
                },
              ),
              ListTile(
                leading: Icon(Icons.brightness_6),
                title: Text("Toggle Dark Mode"),
                onTap: () {
                  setState(() {
                    isDarkMode = !isDarkMode;
                  });
                },
              ),
            ],
          ),
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
                    urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                  ),
                  MarkerLayer(
                    markers: [
                      Marker(
                        width: 80.0,
                        height: 80.0,
                        point: userLocation,
                        child: Icon(
                          Icons.person_pin_circle,
                          color: Colors.blue,
                          size: 40.0,
                        ),
                      )
                    ],
                  ),
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
        bottomNavigationBar: BottomNavigationBar(
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.map), label: "Map"),
            BottomNavigationBarItem(icon: Icon(Icons.settings), label: "Settings"),
          ],
          onTap: (index) {
            if (index == 1) {
              print("Navigating to settings...");
            }
          },
        ),
      ),
    );
  }
}
