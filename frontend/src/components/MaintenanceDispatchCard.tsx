import React from 'react';
import { Clock, Wrench, ShieldAlert, CheckCircle, AlertOctagon } from 'lucide-react';
import { MaintenanceDispatch } from '../types';

interface MaintenanceDispatchCardProps {
  dispatch?: MaintenanceDispatch;
}

export const MaintenanceDispatchCard: React.FC<MaintenanceDispatchCardProps> = ({ dispatch }) => {
  const priority = dispatch?.work_order_priority ?? 'P4_ROUTINE_MONITORING';
  const sla = dispatch?.sla_target_timeframe ?? '180 days routine cycle';
  const rationale = dispatch?.dispatch_rationale ?? 'No acute structural or hydraulic impediments detected.';
  const maxGrade = dispatch?.max_defect_grade_observed ?? 1;
  const criticalCount = dispatch?.critical_defects_count ?? 0;

  const getPriorityConfig = (p: string) => {
    switch (p.toUpperCase()) {
      case 'P1_EMERGENCY':
        return {
          label: 'P1 - EMERGENCY DISPATCH',
          bg: 'rgba(239, 68, 68, 0.2)',
          color: 'var(--color-critical)',
          border: 'rgba(239, 68, 68, 0.5)',
          icon: AlertOctagon,
        };
      case 'P2_HIGH_PRIORITY':
        return {
          label: 'P2 - HIGH PRIORITY',
          bg: 'rgba(249, 115, 22, 0.2)',
          color: 'var(--color-severe)',
          border: 'rgba(249, 115, 22, 0.5)',
          icon: ShieldAlert,
        };
      case 'P3_MEDIUM_PRIORITY':
        return {
          label: 'P3 - MEDIUM PRIORITY',
          bg: 'rgba(234, 179, 8, 0.2)',
          color: 'var(--color-moderate)',
          border: 'rgba(234, 179, 8, 0.5)',
          icon: Clock,
        };
      default:
        return {
          label: 'P4 - ROUTINE MONITORING',
          bg: 'rgba(16, 185, 129, 0.2)',
          color: 'var(--color-good)',
          border: 'rgba(16, 185, 129, 0.5)',
          icon: CheckCircle,
        };
    }
  };

  const config = getPriorityConfig(priority);
  const IconComponent = config.icon;

  return (
    <div className="card">
      <div className="card-title">
        <span>Maintenance Prioritization</span>
        <Wrench size={16} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: config.bg,
            border: `1px solid ${config.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: config.color,
            flexShrink: 0,
          }}
        >
          <IconComponent size={22} />
        </div>
        <div>
          <span
            className="badge"
            style={{
              backgroundColor: config.bg,
              color: config.color,
              border: `1px solid ${config.border}`,
              fontSize: '0.82rem',
              padding: '4px 10px',
            }}
          >
            {config.label}
          </span>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            SLA: <strong style={{ color: 'var(--text-main)' }}>{sla}</strong>
          </div>
        </div>
      </div>

      <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: '1.45' }}>
        {rationale}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
        <div style={{ padding: '8px 12px', background: 'var(--bg-surface)', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Max Grade Observed</div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: maxGrade >= 4 ? 'var(--color-critical)' : maxGrade >= 3 ? 'var(--color-moderate)' : 'var(--color-good)' }}>
            Grade {maxGrade} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-dim)' }}>/ 5</span>
          </div>
        </div>

        <div style={{ padding: '8px 12px', background: 'var(--bg-surface)', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Critical Defects (G4-5)</div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: criticalCount > 0 ? 'var(--color-critical)' : 'var(--color-good)' }}>
            {criticalCount} {criticalCount === 1 ? 'Defect' : 'Defects'}
          </div>
        </div>
      </div>
    </div>
  );
};
