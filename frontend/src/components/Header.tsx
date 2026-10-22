import React from 'react';
import { Activity, Cpu, HardDrive, Map, Video, ClipboardList, PlusCircle } from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  activeTab: 'dashboard' | 'inspections' | 'queue' | 'gis';
  setActiveTab: (tab: 'dashboard' | 'inspections' | 'queue' | 'gis') => void;
  systemHealth: SystemHealth | null;
  onOpenUpload: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  systemHealth,
  onOpenUpload,
}) => {
  return (
    <header className="top-nav">
      <div className="nav-brand">
        <div className="nav-logo-icon">
          <Activity size={22} />
        </div>
        <div>
          <h1 className="nav-title">Smart Drainage AI</h1>
          <p className="nav-subtitle">CCTV Defect Intelligence & Predictive Maintenance</p>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <Activity size={16} />
          <span>Dashboard</span>
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'inspections' ? 'active' : ''}`}
          onClick={() => setActiveTab('inspections')}
        >
          <Video size={16} />
          <span>Inspections</span>
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'queue' ? 'active' : ''}`}
          onClick={() => setActiveTab('queue')}
        >
          <ClipboardList size={16} />
          <span>Work Order Queue</span>
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'gis' ? 'active' : ''}`}
          onClick={() => setActiveTab('gis')}
        >
          <Map size={16} />
          <span>GIS Network</span>
        </button>
      </nav>

      <div className="nav-actions">
        {systemHealth && (
          <div className="gpu-badge" title={`Model: ${systemHealth.model_checkpoint} | Free VRAM: ${systemHealth.vram_free_gb ?? 0}GB`}>
            <span className="gpu-dot"></span>
            <Cpu size={14} />
            <span>{systemHealth.device}</span>
          </div>
        )}

        <button className="btn-primary" onClick={onOpenUpload}>
          <PlusCircle size={16} />
          <span>New Inspection</span>
        </button>
      </div>
    </header>
  );
};
