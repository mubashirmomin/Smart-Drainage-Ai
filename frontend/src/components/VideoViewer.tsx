import React, { useRef } from 'react';
import { Eye, AlertTriangle, CheckCircle2, Film, Loader2, AlertCircle } from 'lucide-react';
import { AssetInspectionMeta, DefectItem } from '../types';

interface VideoViewerProps {
  inspectionId: string;
  status?: string;
  errorMessage?: string;
  meta?: AssetInspectionMeta;
  defects: DefectItem[];
}

export const VideoViewer: React.FC<VideoViewerProps> = ({
  inspectionId,
  status = 'COMPLETED',
  errorMessage,
  meta,
  defects,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const videoSrc = `/api/v1/inspections/${inspectionId}/video`;

  const handleSeek = (timeSec: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, timeSec - 0.5);
      videoRef.current.play().catch(() => {});
    }
  };

  const opticalStatus = meta?.inspection_optical_status ?? 'EXCELLENT';
  const degradedPct = meta?.degraded_footage_pct ?? 0;
  const isOpticalDegraded = degradedPct > 20 || opticalStatus.includes('DEGRADED') || opticalStatus.includes('BLUR');

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div className="card-title">
        <span>CCTV Inspection Player & Optical AI</span>
        <Film size={16} />
      </div>

      {/* State A: AI Processing in progress */}
      {(status === 'PROCESSING' || status === 'PENDING') && (
        <div
          style={{
            height: '340px',
            backgroundColor: '#090d16',
            borderRadius: '12px',
            border: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            textAlign: 'center',
          }}
        >
          <Loader2 size={44} className="spin" style={{ color: 'var(--accent-blue)', marginBottom: '16px' }} />
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
            AI Pipeline Processing Video Frames...
          </h4>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', maxWidth: '440px', lineHeight: '1.5' }}>
            Ultralytics YOLO11s is detecting visible defects while ByteTrack associates spatial trajectories. The annotated video and condition report will appear here automatically.
          </p>
        </div>
      )}

      {/* State B: Processing Failed */}
      {status === 'FAILED' && (
        <div
          style={{
            height: '340px',
            backgroundColor: '#090d16',
            borderRadius: '12px',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            textAlign: 'center',
          }}
        >
          <AlertCircle size={44} style={{ color: 'var(--color-critical)', marginBottom: '14px' }} />
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fca5a5', marginBottom: '8px' }}>
            Inspection Processing Interrupted
          </h4>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', maxWidth: '440px', lineHeight: '1.5' }}>
            {errorMessage || 'The background analysis was interrupted. Please select a completed inspection or run a new inspection.'}
          </p>
        </div>
      )}

      {/* State C: Processing Completed -> Full Video Player */}
      {status === 'COMPLETED' && (
        <>
          <div className="video-wrapper">
            <video
              ref={videoRef}
              className="video-player"
              controls
              playsInline
              src={videoSrc}
            >
              Your browser does not support the video tag.
            </video>
          </div>

          {/* Optical Quality Diagnostic Banner */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              padding: '10px 14px',
              borderRadius: '8px',
              backgroundColor: isOpticalDegraded ? 'rgba(234, 179, 8, 0.1)' : 'rgba(16, 185, 129, 0.1)',
              border: `1px solid ${isOpticalDegraded ? 'rgba(234, 179, 8, 0.3)' : 'rgba(16, 185, 129, 0.25)'}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {isOpticalDegraded ? (
                <AlertTriangle size={18} style={{ color: 'var(--color-moderate)' }} />
              ) : (
                <CheckCircle2 size={18} style={{ color: 'var(--color-good)' }} />
              )}
              <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>
                Optical Quality: {opticalStatus}
              </span>
            </div>

            <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              <span>Frames: <strong style={{ color: 'var(--text-main)' }}>{meta?.total_frames_analyzed ?? 0}</strong></span>
              <span>Degraded: <strong style={{ color: degradedPct > 0 ? 'var(--color-moderate)' : 'var(--color-good)' }}>{degradedPct.toFixed(1)}%</strong></span>
              <span>Duration: <strong style={{ color: 'var(--text-main)' }}>{meta?.video_duration_seconds?.toFixed(1) ?? 0}s</strong></span>
            </div>
          </div>

          {/* Quick Jump Timeline */}
          {defects.length > 0 && (
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
                Direct Defect Markers (Click to Seek):
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {defects.map((d) => {
                  const sec = d.first_time_sec ?? 0;
                  return (
                    <button
                      key={d.defect_id}
                      onClick={() => handleSeek(sec)}
                      style={{
                        backgroundColor: 'var(--bg-surface)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        padding: '5px 10px',
                        fontSize: '0.76rem',
                        color: 'var(--text-main)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                      title={`Jump to ${d.class_name} at ${sec.toFixed(1)}s`}
                    >
                      <Eye size={12} style={{ color: 'var(--accent-blue)' }} />
                      <span>
                        {d.class_name} ({sec.toFixed(1)}s)
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
