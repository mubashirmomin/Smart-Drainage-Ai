import React, { useState } from 'react';
import { Video, Loader2, ArrowRight, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { InspectionSummary } from '../types';

interface InspectionsListProps {
  inspections: InspectionSummary[];
  onSelectInspection: (id: string) => void;
  selectedId?: string;
}

export const InspectionsList: React.FC<InspectionsListProps> = ({
  inspections,
  onSelectInspection,
  selectedId,
}) => {
  const [filterText, setFilterText] = useState('');

  const filtered = inspections.filter((insp) => {
    const q = filterText.toLowerCase();
    return (
      insp.inspection_id.toLowerCase().includes(q) ||
      insp.pipe_id.toLowerCase().includes(q) ||
      insp.street_name.toLowerCase().includes(q) ||
      insp.ward.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return { label: 'COMPLETED', color: 'var(--color-good)', bg: 'rgba(16, 185, 129, 0.15)', icon: CheckCircle2 };
      case 'PROCESSING':
        return { label: 'PROCESSING', color: 'var(--accent-blue)', bg: 'rgba(56, 189, 248, 0.15)', icon: Loader2, spin: true };
      case 'PENDING':
        return { label: 'QUEUED', color: 'var(--color-moderate)', bg: 'rgba(234, 179, 8, 0.15)', icon: Clock };
      default:
        return { label: 'FAILED', color: 'var(--color-critical)', bg: 'rgba(239, 68, 68, 0.15)', icon: AlertCircle };
    }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Underground CCTV Inspection History</h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            All automated robotic crawler runs and defect detection logs across Mumbai wards.
          </p>
        </div>

        <div>
          <input
            type="text"
            placeholder="Search pipe, street, or ward..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{
              padding: '8px 14px',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-main)',
              border: '1px solid var(--border-color)',
              fontSize: '0.85rem',
              minWidth: '260px',
            }}
          />
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Inspection ID</th>
              <th>Pipe & Street</th>
              <th>Ward</th>
              <th>Status</th>
              <th>PCI Score</th>
              <th>Blockage %</th>
              <th>Defects</th>
              <th>Priority</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  No inspections match your search filter.
                </td>
              </tr>
            ) : (
              filtered.map((insp) => {
                const statusMeta = getStatusBadge(insp.status);
                const StatusIcon = statusMeta.icon;
                const isSelected = insp.inspection_id === selectedId;

                return (
                  <tr
                    key={insp.inspection_id}
                    style={{
                      backgroundColor: isSelected ? 'rgba(56, 189, 248, 0.06)' : undefined,
                    }}
                  >
                    <td>
                      <div style={{ fontWeight: 700, color: 'var(--text-main)', fontFamily: 'var(--font-mono)', fontSize: '0.84rem' }}>
                        {insp.inspection_id}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                        {insp.video_filename}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{insp.pipe_id}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{insp.street_name}</div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{insp.ward}</span>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: statusMeta.bg,
                          color: statusMeta.color,
                          border: `1px solid ${statusMeta.color}`,
                          gap: '5px',
                        }}
                      >
                        <StatusIcon size={12} className={statusMeta.spin ? 'spin' : ''} />
                        <span>{statusMeta.label}</span>
                      </span>
                    </td>
                    <td>
                      <strong
                        style={{
                          color:
                            insp.pci_score !== undefined
                              ? insp.pci_score >= 70
                                ? 'var(--color-good)'
                                : insp.pci_score >= 50
                                ? 'var(--color-moderate)'
                                : 'var(--color-critical)'
                              : 'var(--text-dim)',
                        }}
                      >
                        {insp.pci_score !== undefined ? `${insp.pci_score}/100` : '—'}
                      </strong>
                    </td>
                    <td>{insp.blockage_percentage !== undefined ? `${insp.blockage_percentage.toFixed(1)}%` : '—'}</td>
                    <td>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '12px',
                          backgroundColor: insp.total_defects > 0 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                          color: insp.total_defects > 0 ? 'var(--color-critical)' : 'var(--color-good)',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                        }}
                      >
                        {insp.total_defects}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-main)' }}>
                        {insp.priority || '—'}
                      </span>
                    </td>
                    <td>
                      <button
                        className={isSelected ? 'btn-primary' : 'btn-secondary'}
                        style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                        onClick={() => onSelectInspection(insp.inspection_id)}
                      >
                        <span>View</span>
                        <ArrowRight size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
