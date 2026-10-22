import React, { useState } from 'react';
import { ClipboardList, AlertOctagon, ShieldAlert, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import { WorkOrderQueueResponse, WorkOrderItem } from '../types';

interface WorkOrderQueueProps {
  queueData: WorkOrderQueueResponse | null;
  onSelectInspection: (inspectionId: string) => void;
}

export const WorkOrderQueue: React.FC<WorkOrderQueueProps> = ({ queueData, onSelectInspection }) => {
  const [selectedFilter, setSelectedFilter] = useState<'ALL' | 'P1' | 'P2' | 'P3' | 'P4'>('ALL');

  if (!queueData) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading Municipal Work Order Queue...</p>
      </div>
    );
  }

  const { summary, work_order_queue } = queueData;

  const allOrders: { priority: string; item: WorkOrderItem }[] = [
    ...(work_order_queue.P1_EMERGENCY || []).map((item) => ({ priority: 'P1_EMERGENCY', item })),
    ...(work_order_queue.P2_HIGH_PRIORITY || []).map((item) => ({ priority: 'P2_HIGH_PRIORITY', item })),
    ...(work_order_queue.P3_MEDIUM_PRIORITY || []).map((item) => ({ priority: 'P3_MEDIUM_PRIORITY', item })),
    ...(work_order_queue.P4_ROUTINE_MONITORING || []).map((item) => ({ priority: 'P4_ROUTINE_MONITORING', item })),
  ];

  const filteredOrders = allOrders.filter((o) => {
    if (selectedFilter === 'ALL') return true;
    if (selectedFilter === 'P1') return o.priority === 'P1_EMERGENCY';
    if (selectedFilter === 'P2') return o.priority === 'P2_HIGH_PRIORITY';
    if (selectedFilter === 'P3') return o.priority === 'P3_MEDIUM_PRIORITY';
    if (selectedFilter === 'P4') return o.priority === 'P4_ROUTINE_MONITORING';
    return true;
  });

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'P1_EMERGENCY':
        return { label: 'P1 Emergency', color: 'var(--color-critical)', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.4)' };
      case 'P2_HIGH_PRIORITY':
        return { label: 'P2 High', color: 'var(--color-severe)', bg: 'rgba(249, 115, 22, 0.15)', border: 'rgba(249, 115, 22, 0.4)' };
      case 'P3_MEDIUM_PRIORITY':
        return { label: 'P3 Medium', color: 'var(--color-moderate)', bg: 'rgba(234, 179, 8, 0.15)', border: 'rgba(234, 179, 8, 0.4)' };
      default:
        return { label: 'P4 Routine', color: 'var(--color-good)', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.4)' };
    }
  };

  return (
    <div>
      {/* Priority Summary KPI Cards */}
      <div className="metrics-row">
        <div
          className="card"
          onClick={() => setSelectedFilter('P1')}
          style={{ cursor: 'pointer', borderColor: selectedFilter === 'P1' ? 'var(--color-critical)' : 'var(--border-color)' }}
        >
          <div className="card-title">
            <span>P1 Emergency (24h)</span>
            <AlertOctagon size={16} style={{ color: 'var(--color-critical)' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--color-critical)' }}>
            {summary.p1_emergency_count}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Imminent collapse / overflow</div>
        </div>

        <div
          className="card"
          onClick={() => setSelectedFilter('P2')}
          style={{ cursor: 'pointer', borderColor: selectedFilter === 'P2' ? 'var(--color-severe)' : 'var(--border-color)' }}
        >
          <div className="card-title">
            <span>P2 High (72h)</span>
            <ShieldAlert size={16} style={{ color: 'var(--color-severe)' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--color-severe)' }}>
            {summary.p2_high_count}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Heavy obstruction / cracking</div>
        </div>

        <div
          className="card"
          onClick={() => setSelectedFilter('P3')}
          style={{ cursor: 'pointer', borderColor: selectedFilter === 'P3' ? 'var(--color-moderate)' : 'var(--border-color)' }}
        >
          <div className="card-title">
            <span>P3 Medium (30d)</span>
            <Clock size={16} style={{ color: 'var(--color-moderate)' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--color-moderate)' }}>
            {summary.p3_medium_count}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Moderate wear & sediment</div>
        </div>

        <div
          className="card"
          onClick={() => setSelectedFilter('P4')}
          style={{ cursor: 'pointer', borderColor: selectedFilter === 'P4' ? 'var(--color-good)' : 'var(--border-color)' }}
        >
          <div className="card-title">
            <span>P4 Routine (180d)</span>
            <CheckCircle2 size={16} style={{ color: 'var(--color-good)' }} />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--color-good)' }}>
            {summary.p4_routine_count}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Sound operational pipe</div>
        </div>
      </div>

      {/* Filter Tabs & Work Orders List */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Municipal Maintenance Work Order Queue</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Prioritized according to WRc condition indices and BMC monsoon flood risk models.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {(['ALL', 'P1', 'P2', 'P3', 'P4'] as const).map((tier) => (
              <button
                key={tier}
                onClick={() => setSelectedFilter(tier)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  backgroundColor: selectedFilter === tier ? 'var(--border-focus)' : 'var(--bg-surface)',
                  color: selectedFilter === tier ? '#fff' : 'var(--text-muted)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                }}
              >
                {tier}
              </button>
            ))}
          </div>
        </div>

        {filteredOrders.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            <ClipboardList size={32} style={{ marginBottom: '8px' }} />
            <p>No active work orders matching this priority filter.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Priority Tier</th>
                  <th>Pipe ID & Location</th>
                  <th>Ward</th>
                  <th>Health (PCI)</th>
                  <th>Blockage %</th>
                  <th>SLA Timeframe</th>
                  <th>Primary Repair Action</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map(({ priority, item }) => {
                  const badge = getPriorityBadge(priority);
                  return (
                    <tr key={item.inspection_id}>
                      <td>
                        <span
                          className="badge"
                          style={{
                            backgroundColor: badge.bg,
                            color: badge.color,
                            border: `1px solid ${badge.border}`,
                          }}
                        >
                          {badge.label}
                        </span>
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{item.pipe_id}</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{item.street_name}</div>
                      </td>
                      <td>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.ward}</span>
                      </td>
                      <td>
                        <strong
                          style={{
                            color:
                              (item.pci_score ?? 100) >= 70
                                ? 'var(--color-good)'
                                : (item.pci_score ?? 100) >= 50
                                ? 'var(--color-moderate)'
                                : 'var(--color-critical)',
                          }}
                        >
                          {item.pci_score ?? 'N/A'}/100
                        </strong>
                      </td>
                      <td>
                        <span>{(item.blockage_percentage ?? 0).toFixed(1)}%</span>
                      </td>
                      <td style={{ fontSize: '0.82rem', color: 'var(--accent-blue)', fontWeight: 600 }}>
                        {item.sla_timeframe}
                      </td>
                      <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: '280px' }}>
                        {item.primary_repair_actions?.[0] || item.dispatch_rationale}
                      </td>
                      <td>
                        <button
                          className="btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                          onClick={() => onSelectInspection(item.inspection_id)}
                        >
                          <span>Review</span>
                          <ArrowRight size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
