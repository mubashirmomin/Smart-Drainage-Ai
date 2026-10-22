import React, { useState } from 'react';
import { X, Upload, Play, Film, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { PipeAsset } from '../types';
import { runSampleInspection, uploadVideoInspection } from '../services/api';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  pipes: PipeAsset[];
  onInspectionCreated: (inspectionId: string) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  pipes,
  onInspectionCreated,
}) => {
  const [selectedPipe, setSelectedPipe] = useState<string>(pipes[0]?.pipe_id || 'PIPE-MUM-001');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stepMessage, setStepMessage] = useState<string>('');

  if (!isOpen) return null;

  const handleRunSample = async () => {
    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      setStepMessage('Dispatching AI pipeline on benchmark inspection video...');
      const res = await runSampleInspection(selectedPipe);
      setStepMessage('Inspection queued successfully! Processing frames...');
      setTimeout(() => {
        onInspectionCreated(res.inspection_id);
        onClose();
        setIsSubmitting(false);
      }, 1000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to trigger sample inspection.');
      setIsSubmitting(false);
    }
  };

  const handleUploadCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please select an MP4 CCTV video file to analyze.');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      setStepMessage(`Uploading ${selectedFile.name} and initiating ByteTrack inference...`);
      const res = await uploadVideoInspection(selectedFile, selectedPipe);
      setStepMessage('Video uploaded! Inference running in background...');
      setTimeout(() => {
        onInspectionCreated(res.inspection_id);
        onClose();
        setIsSubmitting(false);
      }, 1000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to upload video.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Film size={20} style={{ color: 'var(--accent-blue)' }} />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Initiate CCTV AI Inspection</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', color: 'var(--text-muted)', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {errorMessage && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid var(--color-critical)',
              color: '#fca5a5',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px',
            }}
          >
            <AlertCircle size={16} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Pipe Asset Selector */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Target Drainage Network Pipe:
          </label>
          <select
            value={selectedPipe}
            onChange={(e) => setSelectedPipe(e.target.value)}
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-main)',
              border: '1px solid var(--border-color)',
              fontSize: '0.88rem',
            }}
          >
            {pipes.map((pipe) => (
              <option key={pipe.pipe_id} value={pipe.pipe_id}>
                {pipe.pipe_id} — {pipe.street_name} ({pipe.ward}) [{pipe.diameter_mm}mm]
              </option>
            ))}
          </select>
        </div>

        {/* Option A: Quick Benchmark Demo */}
        <div
          style={{
            backgroundColor: 'rgba(56, 189, 248, 0.05)',
            border: '1px dashed rgba(56, 189, 248, 0.3)',
            borderRadius: '10px',
            padding: '16px',
            marginBottom: '20px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--accent-blue)' }}>
                One-Click Benchmark Video Test
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Runs YOLO11s + ByteTrack on pre-calibrated CCTV sample inspection.
              </div>
            </div>
            <button
              className="btn-primary"
              onClick={handleRunSample}
              disabled={isSubmitting}
              style={{ padding: '8px 14px', fontSize: '0.82rem' }}
            >
              {isSubmitting ? <Loader2 size={15} className="spin" /> : <Play size={15} />}
              <span>Run Benchmark</span>
            </button>
          </div>
        </div>

        <div style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '16px' }}>
          — OR UPLOAD CUSTOM CCTV FOOTAGE —
        </div>

        {/* Option B: Custom File Upload Form */}
        <form onSubmit={handleUploadCustom}>
          <div
            style={{
              border: '2px dashed var(--border-color)',
              borderRadius: '10px',
              padding: '24px',
              textAlign: 'center',
              backgroundColor: 'rgba(255,255,255,0.01)',
              marginBottom: '18px',
              cursor: 'pointer',
            }}
            onClick={() => document.getElementById('cctv-file-input')?.click()}
          >
            <Upload size={32} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
            <div style={{ fontSize: '0.86rem', fontWeight: 600 }}>
              {selectedFile ? selectedFile.name : 'Select or Drop CCTV Video (.mp4)'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
              Standard robotic crawler or push-rod CCTV inspection media
            </div>
            <input
              id="cctv-file-input"
              type="file"
              accept="video/mp4"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
            />
          </div>

          {stepMessage && (
            <div style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', marginBottom: '14px', textAlign: 'center' }}>
              {stepMessage}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting || !selectedFile}
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={16} className="spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Upload size={16} />
                  <span>Upload & Analyze</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
