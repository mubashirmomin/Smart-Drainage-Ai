/**
 * frontend/src/services/api.ts - Typed API Client for FastAPI Backend
 */

import {
  InspectionDetail,
  InspectionSummary,
  PipeAsset,
  SystemHealth,
  WorkOrderQueueResponse,
} from '../types';

const BASE_URL = '/api/v1';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('Failed to fetch system health');
  return res.json();
}

export async function fetchPipes(): Promise<PipeAsset[]> {
  const res = await fetch(`${BASE_URL}/pipes/`);
  if (!res.ok) throw new Error('Failed to fetch drainage pipes');
  return res.json();
}

export async function fetchInspections(): Promise<InspectionSummary[]> {
  const res = await fetch(`${BASE_URL}/inspections/`);
  if (!res.ok) throw new Error('Failed to fetch inspections list');
  return res.json();
}

export async function fetchInspectionDetail(id: string): Promise<InspectionDetail> {
  const res = await fetch(`${BASE_URL}/inspections/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch inspection ${id}`);
  return res.json();
}

export async function fetchWorkOrderQueue(): Promise<WorkOrderQueueResponse> {
  const res = await fetch(`${BASE_URL}/queue`);
  if (!res.ok) throw new Error('Failed to fetch work order queue');
  return res.json();
}

export async function runSampleInspection(pipeId: string = 'PIPE-MUM-001'): Promise<{ inspection_id: string; message: string }> {
  const formData = new FormData();
  formData.append('pipe_id', pipeId);

  const res = await fetch(`${BASE_URL}/inspections/run-sample`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to trigger sample inspection');
  return res.json();
}

export async function uploadVideoInspection(
  file: File,
  pipeId: string,
): Promise<{ inspection_id: string; message: string }> {
  const formData = new FormData();
  formData.append('pipe_id', pipeId);
  formData.append('file', file);

  const res = await fetch(`${BASE_URL}/inspections/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload video');
  }
  return res.json();
}
