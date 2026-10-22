import React from 'react';
import { ShieldAlert, ShieldCheck, Activity } from 'lucide-react';
import { PipeHealthIndices } from '../types';

interface PciGaugeProps {
  health?: PipeHealthIndices;
}

export const PciGaugeCard: React.FC<PciGaugeProps> = ({ health }) => {
  const pci = health?.pci_overall_score ?? 100;
  const sci = health?.structural_index_sci ?? 100;
  const oci = health?.operational_index_oci ?? 100;
  const state = health?.condition_state ?? 'EXCELLENT';

  const getColor = (val: number) => {
    if (val >= 85) return 'var(--color-good)';
    if (val >= 70) return 'var(--accent-blue)';
    if (val >= 50) return 'var(--color-moderate)';
    if (val >= 30) return 'var(--color-severe)';
    return 'var(--color-critical)';
  };

  const pciColor = getColor(pci);

  return (
    <div className="card">
      <div className="card-title">
        <span>Pipe Condition Index (PCI)</span>
        <Activity size={16} />
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '8px' }}>
        <span className="gauge-score" style={{ color: pciColor }}>
          {pci}
        </span>
        <span style={{ fontSize: '1.1rem', color: 'var(--text-muted)', fontWeight: 600 }}>/ 100</span>
        <span
          className="badge"
          style={{
            backgroundColor: `rgba(${pci >= 70 ? '16, 185, 129' : pci >= 50 ? '234, 179, 8' : '239, 68, 68'}, 0.15)`,
            color: pciColor,
            border: `1px solid ${pciColor}`,
            marginLeft: 'auto',
          }}
        >
          {state}
        </span>
      </div>

      <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
        {health?.condition_description || 'Pipe operating in normal condition.'}
      </p>

      {/* Structural Index SCI */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Structural Health (SCI)</span>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{sci}/100</span>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${sci}%`, backgroundColor: getColor(sci) }}
          />
        </div>
      </div>

      {/* Operational Index OCI */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Hydraulic Cleanliness (OCI)</span>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{oci}/100</span>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${oci}%`, backgroundColor: getColor(oci) }}
          />
        </div>
      </div>
    </div>
  );
};
