import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { Map, Layers, Navigation, AlertTriangle } from 'lucide-react';
import { PipeAsset } from '../types';

interface GisPipeMapProps {
  pipes: PipeAsset[];
  onSelectPipe?: (pipeId: string) => void;
}

export const GisPipeMap: React.FC<GisPipeMapProps> = ({ pipes, onSelectPipe }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const getPipeColor = (pci?: number, criticality?: string) => {
    if (pci !== undefined) {
      if (pci >= 80) return '#10b981'; // Green
      if (pci >= 60) return '#38bdf8'; // Blue
      if (pci >= 40) return '#eab308'; // Yellow
      if (pci >= 20) return '#f97316'; // Orange
      return '#ef4444'; // Red
    }
    if (criticality === 'HIGH') return '#f97316';
    return '#38bdf8';
  };

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Center on Mumbai drainage network (Dadar / Bandra / Kurla)
    const mumbaiCenter: [number, number] = [19.045, 72.85];
    const map = L.map(mapContainerRef.current, {
      center: mumbaiCenter,
      zoom: 12,
      scrollWheelZoom: true,
    });

    mapInstanceRef.current = map;

    // Dark control-room map tiles (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    const bounds = L.latLngBounds([]);

    // Add pipes and manholes
    pipes.forEach((pipe) => {
      const color = getPipeColor(pipe.latest_pci, pipe.criticality);
      const startPoint: [number, number] = pipe.start_coords;
      const endPoint: [number, number] = pipe.end_coords;

      bounds.extend(startPoint);
      bounds.extend(endPoint);

      // Start Manhole Circle
      const startMarker = L.circleMarker(startPoint, {
        radius: 6,
        color: '#fff',
        fillColor: color,
        fillOpacity: 0.9,
        weight: 2,
      }).addTo(map);

      startMarker.bindPopup(`
        <div style="color: #0f172a; font-family: sans-serif; font-size: 12px;">
          <strong>Manhole:</strong> ${pipe.start_manhole}<br/>
          <strong>Pipe ID:</strong> ${pipe.pipe_id}<br/>
          <strong>Street:</strong> ${pipe.street_name}
        </div>
      `);

      // End Manhole Circle
      const endMarker = L.circleMarker(endPoint, {
        radius: 6,
        color: '#fff',
        fillColor: color,
        fillOpacity: 0.9,
        weight: 2,
      }).addTo(map);

      endMarker.bindPopup(`
        <div style="color: #0f172a; font-family: sans-serif; font-size: 12px;">
          <strong>Manhole:</strong> ${pipe.end_manhole}<br/>
          <strong>Pipe ID:</strong> ${pipe.pipe_id}<br/>
          <strong>Street:</strong> ${pipe.street_name}
        </div>
      `);

      // Pipe segment Polyline
      const polyline = L.polyline([startPoint, endPoint], {
        color: color,
        weight: 5,
        opacity: 0.85,
      }).addTo(map);

      polyline.bindPopup(`
        <div style="color: #0f172a; font-family: sans-serif; font-size: 13px; line-height: 1.4;">
          <h4 style="margin: 0 0 4px 0; color: #0369a1;">${pipe.pipe_id}</h4>
          <strong>Street:</strong> ${pipe.street_name} (${pipe.ward})<br/>
          <strong>Material:</strong> ${pipe.material} | ${pipe.diameter_mm} mm<br/>
          <strong>Length:</strong> ${pipe.length_meters} m<br/>
          <strong>Latest PCI:</strong> <strong style="color: ${color};">${pipe.latest_pci ?? 'Uninspected'}</strong><br/>
          <strong>Condition:</strong> ${pipe.latest_condition_state ?? 'PENDING'}<br/>
          <strong>Priority:</strong> ${pipe.latest_priority ?? 'NORMAL'}
        </div>
      `);
    });

    if (pipes.length > 0 && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [pipes]);

  const handleFocusPipe = (pipe: PipeAsset) => {
    if (mapInstanceRef.current) {
      const bounds = L.latLngBounds([pipe.start_coords, pipe.end_coords]);
      mapInstanceRef.current.fitBounds(bounds, { padding: [80, 80], maxZoom: 15 });
    }
    if (onSelectPipe) {
      onSelectPipe(pipe.pipe_id);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
      {/* Map Element */}
      <div className="card" style={{ padding: '16px' }}>
        <div className="card-title">
          <span>Brihanmumbai Municipal GIS Underground Network</span>
          <Map size={16} />
        </div>
        <div ref={mapContainerRef} className="map-container" />
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginTop: '12px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          <span>Legend (PCI):</span>
          <span style={{ color: '#10b981' }}>● 80-100 (Good)</span>
          <span style={{ color: '#38bdf8' }}>● 60-79 (Fair)</span>
          <span style={{ color: '#eab308' }}>● 40-59 (Moderate)</span>
          <span style={{ color: '#f97316' }}>● 20-39 (Severe)</span>
          <span style={{ color: '#ef4444' }}>● &lt;20 (Critical)</span>
        </div>
      </div>

      {/* Asset Network Sidebar */}
      <div className="card" style={{ padding: '16px', display: 'flex', flexDirection: 'column' }}>
        <div className="card-title">
          <span>Monitored Assets ({pipes.length})</span>
          <Layers size={16} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto', maxHeight: '490px' }}>
          {pipes.map((pipe) => {
            const color = getPipeColor(pipe.latest_pci, pipe.criticality);
            return (
              <div
                key={pipe.pipe_id}
                onClick={() => handleFocusPipe(pipe)}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '12px',
                  cursor: 'pointer',
                  transition: 'border-color 0.2s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-main)' }}>{pipe.pipe_id}</span>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: color,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(255,255,255,0.05)',
                    }}
                  >
                    PCI: {pipe.latest_pci ?? 'N/A'}
                  </span>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {pipe.street_name} ({pipe.ward})
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '6px' }}>
                  <span>{pipe.diameter_mm}mm {pipe.material}</span>
                  <span>{pipe.length_meters}m</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
