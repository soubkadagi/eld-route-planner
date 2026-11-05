import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function RouteMap({ geometry }) {
  if (!geometry) return null;
  const startCoords = [geometry.coordinates[0][1], geometry.coordinates[0][0]];

  return (
    <div style={{ height: '360px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #cbd5e1' }}>
      <MapContainer center={startCoords} zoom={5} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeoJSON data={{ type: 'Feature', geometry }} style={{ color: '#2563eb', weight: 4 }} />
      </MapContainer>
    </div>
  );
}
