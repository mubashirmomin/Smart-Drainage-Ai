import React, { useState } from 'react';
import { Layers, LayoutGrid, List, Wrench, Clock, AlertCircle } from 'lucide-react';
import { DefectItem } from '../types';

interface DefectInventoryProps {
  inspectionId: string;
  defects: DefectItem[];
}

export const DefectInventory: React.FC<DefectInventoryProps> = ({ inspectionId, defects }) => {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  const getGradeBadge = (grade: number) => {
    switch (grade) {
      case 5:
        return { label: 'Grade 5 (Imminent Failure)', color: 'var(--color-critical)', bg: 'rgba(239, 68, 68, 0.15)' };
      case 4:
        return { label: 'Grade 4 (Extensive)', color: 'var(--color-severe)', bg: 'rgba(249, 115, 22, 0.15)' };
      case 3:
        return { label: 'Grade 3 (Moderate)', color: 'var(--color-moderate)', bg: 'rgba(234, 179, 8, 0.15)' };
      case 2:
        return { label: 'Grade 2 (Minor)', color: 'var(--accent-blue)', bg: 'rgba(56, 189, 248, 0.15)' };
      default:
        return { label: 'Grade 1 (Superficial)', color: 'var(--color-good)', bg: 'rgba(16, 185, 129, 0.15)' };
    }
  };

  return (
    <div className="card" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Deduplicated Defect Inventory</h3>
            <span
              className="badge"
              style={{
                backgroundColor: defects.length > 0 ? 'rgba(56, 189, 248, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                color: defects.length > 0 ? 'var(--accent-blue)' : 'var(--color-good)',
                border: `1px solid ${defects.length > 0 ? 'var(--accent-blue)' : 'var(--color-good)'}`,
              }}
            >
              {defects.length} {defects.length === 1 ? 'Defect' : 'Defects'} Verified
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Multi-frame tracking eliminates duplicate counts across continuous camera travel.
          </p>
        </div>

        {/* View Toggle */}
        <div style={{ display: 'flex', gap: '6px', backgroundColor: 'var(--bg-surface)', padding: '4px', borderRadius: '8px' }}>
          <button
            onClick={() => setViewMode('grid')}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              backgroundColor: viewMode === 'grid' ? 'var(--border-focus)' : 'transparent',
              color: viewMode === 'grid' ? '#fff' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem',
            }}
          >
            <LayoutGrid size={15} />
            <span>Cards</span>
          </button>
          <button
            onClick={() => setViewMode('table')}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              backgroundColor: viewMode === 'table' ? 'var(--border-focus)' : 'transparent',
              color: viewMode === 'table' ? '#fff' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem',
            }}
          >
            <List size={15} />
            <span>Table</span>
          </button>
        </div>
      </div>

      {defects.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
          <Layers size={36} style={{ color: 'var(--color-good)', marginBottom: '12px' }} />
          <p style={{ fontWeight: 600, color: 'var(--text-main)' }}>No Structural or Hydraulic Defects Found</p>
          <p style={{ fontSize: '0.84rem' }}>The AI model verified this drainage pipeline meets operational safety criteria.</p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="defects-grid">
          {defects.map((defect) => {
            const badge = getGradeBadge(defect.severity_grade);
            const thumbUrl = defect.thumbnail_url
              ? `/api/v1/inspections/${inspectionId}/thumbnails/${defect.thumbnail_url}`
              : null;

            return (
              <div key={defect.defect_id} className="defect-card">
                {thumbUrl ? (
                  <img
                    src={thumbUrl}
                    alt={defect.class_name}
                    className="defect-card-thumb"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <div
                    style={{
                      height: '140px',
                      backgroundColor: 'var(--bg-surface)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-dim)',
                    }}
                  >
                    <Layers size={32} />
                  </div>
                )}

                <div className="defect-card-body">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.98rem' }}>{defect.class_name}</span>
                    <span
                      className="badge"
                      style={{
                        backgroundColor: badge.bg,
                        color: badge.color,
                        border: `1px solid ${badge.color}`,
                        fontSize: '0.72rem',
                      }}
                    >
                      {badge.label}
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        backgroundColor: defect.failure_mode === 'STRUCTURAL' ? 'rgba(249, 115, 22, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                        color: defect.failure_mode === 'STRUCTURAL' ? 'var(--color-severe)' : 'var(--accent-blue)',
                        fontWeight: 600,
                      }}
                    >
                      {defect.failure_mode}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      Conf: {(defect.detection_confidence * 100).toFixed(0)}%
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      Area: {defect.max_area_percentage.toFixed(1)}%
                    </span>
                  </div>

                  <div
                    style={{
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      padding: '10px',
                      borderRadius: '8px',
                      fontSize: '0.78rem',
                      marginBottom: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-blue)', fontWeight: 600, marginBottom: '4px' }}>
                      <Wrench size={13} />
                      <span>Prescribed Civil Repair:</span>
                    </div>
                    <div style={{ color: 'var(--text-main)', lineHeight: '1.4' }}>
                      {defect.recommended_repair_action}
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    <span>Persisted: {defect.persistence_seconds.toFixed(1)}s</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> Target SLA: {defect.target_resolution_days}d
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Defect Class</th>
                <th>Failure Mode</th>
                <th>Severity Grade</th>
                <th>Max Area %</th>
                <th>Persistence</th>
                <th>Target SLA</th>
                <th>Engineering Repair Action</th>
              </tr>
            </thead>
            <tbody>
              {defects.map((defect) => {
                const badge = getGradeBadge(defect.severity_grade);
                return (
                  <tr key={defect.defect_id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{defect.class_name}</td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.74rem',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          backgroundColor: defect.failure_mode === 'STRUCTURAL' ? 'rgba(249, 115, 22, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                          color: defect.failure_mode === 'STRUCTURAL' ? 'var(--color-severe)' : 'var(--accent-blue)',
                          fontWeight: 600,
                        }}
                      >
                        {defect.failure_mode}
                      </span>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.color}`,
                          fontSize: '0.72rem',
                        }}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td>{defect.max_area_percentage.toFixed(1)}%</td>
                    <td>{defect.persistence_seconds.toFixed(1)}s</td>
                    <td>{defect.target_resolution_days} Days</td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: '320px' }}>
                      {defect.recommended_repair_action}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
