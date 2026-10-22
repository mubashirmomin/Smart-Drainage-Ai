import React from 'react';
import { Droplets, AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react';
import { HydraulicAssessment } from '../types';

interface BlockageRiskCardProps {
  hydraulic?: HydraulicAssessment;
}

export const BlockageRiskCard: React.FC<BlockageRiskCardProps> = ({ hydraulic }) => {
  const blockage = hydraulic?.blockage_percentage ?? 0;
  const flowLoss = hydraulic?.estimated_flow_loss_pct ?? 0;
  const risk = hydraulic?.monsoon_overflow_risk ?? 'LOW';
  const tier = hydraulic?.blockage_severity_tier ?? 'CLEAR';
  const cleaningRequired = hydraulic?.immediate_cleaning_required ?? false;

  const getRiskBadge = (r: string) => {
    switch (r.toUpperCase()) {
      case 'CRITICAL':
        return { label: 'CRITICAL OVERFLOW RISK', bg: 'rgba(239, 68, 68, 0.2)', color: 'var(--color-critical)', border: 'var(--color-critical)' };
      case 'HIGH':
        return { label: 'HIGH MONSOON RISK', bg: 'rgba(249, 115, 22, 0.2)', color: 'var(--color-severe)', border: 'var(--color-severe)' };
      case 'MODERATE':
        return { label: 'MODERATE SURCHARGE RISK', bg: 'rgba(234, 179, 8, 0.2)', color: 'var(--color-moderate)', border: 'var(--color-moderate)' };
      default:
        return { label: 'LOW / OPTIMAL CONVEYANCE', bg: 'rgba(16, 185, 129, 0.2)', color: 'var(--color-good)', border: 'var(--color-good)' };
    }
  };

  const riskBadge = getRiskBadge(risk);

  return (
    <div className="card">
      <div className="card-title">
        <span>Hydraulic Conveyance</span>
        <Droplets size={16} />
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '8px' }}>
        <span
          className="gauge-score"
          style={{
            color: blockage > 40 ? 'var(--color-critical)' : blockage > 20 ? 'var(--color-severe)' : blockage > 10 ? 'var(--color-moderate)' : 'var(--color-good)',
          }}
        >
          {blockage.toFixed(1)}%
        </span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Cross-Sectional Choke</span>
        <span
          className="badge"
          style={{
            backgroundColor: riskBadge.bg,
            color: riskBadge.color,
            border: `1px solid ${riskBadge.border}`,
            marginLeft: 'auto',
          }}
        >
          {riskBadge.label}
        </span>
      </div>

      <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
        Estimated flow reduction: <strong style={{ color: 'var(--text-main)' }}>{flowLoss.toFixed(1)}%</strong> of hydraulic design capacity. Tier: <strong style={{ color: 'var(--accent-blue)' }}>{tier}</strong>.
      </p>

      {/* Hydraulic Obstruction Progress Bar */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Hydraulic Obstruction Ratio</span>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{blockage.toFixed(1)}%</span>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{
              width: `${Math.min(blockage, 100)}%`,
              backgroundColor: blockage > 40 ? 'var(--color-critical)' : blockage > 20 ? 'var(--color-severe)' : blockage > 10 ? 'var(--color-moderate)' : 'var(--color-good)',
            }}
          />
        </div>
      </div>

      {cleaningRequired ? (
        <div
          style={{
            padding: '10px 14px',
            borderRadius: '8px',
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            marginBottom: '14px',
          }}
        >
          <AlertTriangle size={18} style={{ color: 'var(--color-critical)', flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.8rem', color: '#fca5a5' }}>
            <strong>Action Required:</strong> {hydraulic?.recommended_hydraulic_action || 'Immediate de-silting and hydro-jetting recommended before monsoon rainfall.'}
          </div>
        </div>
      ) : (
        <div
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            backgroundColor: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '14px',
            fontSize: '0.8rem',
            color: 'var(--color-good)',
          }}
        >
          <CheckCircle2 size={16} />
          <span>Flow capacity within standard municipal clearance limits.</span>
        </div>
      )}

      {hydraulic?.primary_blockage_cause && (
        <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
          Primary cause: <span style={{ color: 'var(--text-main)' }}>{hydraulic.primary_blockage_cause}</span> ({hydraulic.flow_impeding_defects_count} defect(s) obstructing flow)
        </div>
      )}
    </div>
  );
};
