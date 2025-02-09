// Import required libraries
import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, ImageOverlay } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import mqtt from "mqtt";
import "./styles.css";

const MQTT_BROKER = "wss://labserver.sense-campus.gr:9002"; // Replace with your MQTT broker
const MQTT_TOPIC = "image";
const MAP_CENTER = [38.2466, 21.7346]; // Centered at Patras, Greece
const MAP_BOUNDS = [
  [38.2, 21.68],
  [38.29, 21.79],
];

const HeatmapPWA = () => {
  const [imageData, setImageData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState(
    "Connecting to MQTT..."
  );
  const [imageStatus, setImageStatus] = useState("Waiting for heatmap data...");
  const [mqttClient, setMqttClient] = useState(null);

  useEffect(() => {
    if (!mqttClient) {
      const client = mqtt.connect(MQTT_BROKER);

      client.on("connect", () => {
        console.log("Connected to MQTT");
        setConnectionStatus("Connected to MQTT");
        client.subscribe(MQTT_TOPIC, (err) => {
          if (err) {
            console.error("MQTT Subscription Error:", err);
            setConnectionStatus("Subscription Failed");
          } else {
            console.log(`Subscribed to ${MQTT_TOPIC}`);
          }
        });
      });

      client.on("error", (err) => {
        console.error("MQTT Connection Error:", err);
        setConnectionStatus("Failed to connect to MQTT");
        client.end();
      });

      client.on("message", (topic, message) => {
        if (topic === MQTT_TOPIC) {
          const base64Image = message.toString();
          setImageData(`data:image/png;base64,${base64Image}`);
          setImageStatus("Heatmap image received and loaded");
        }
      });

      setMqttClient(client);
    }

    return () => {
      if (mqttClient) {
        mqttClient.end();
        setConnectionStatus("Disconnected from MQTT");
      }
    };
  }, [mqttClient]); // Ensures useEffect runs only once

  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <div className="navbar">
        <h1>APARS Demo</h1>
        <div className="menu">
          <button id="menuBtn">Menu</button>
          <button id="toggleOverlay">Toggle Overlay</button>
        </div>
      </div>

      {/* Connection and Image Status */}
      <h2>{connectionStatus}</h2>
      <h3>{imageStatus}</h3>

      {/* Map Container */}
      <div className="map-container">
        <MapContainer
          center={MAP_CENTER}
          zoom={13}
          style={{ width: "100%", height: "100%" }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {imageData && (
            <ImageOverlay url={imageData} bounds={MAP_BOUNDS} opacity={0.6} />
          )}
        </MapContainer>
      </div>
    </div>
  );
};

export default HeatmapPWA;
