import { ScanJob, ScanResult, WebScanResult, DashboardStats } from '../types';
import { API_BASE_URL } from '../config/runtime';

const API_BASE = API_BASE_URL;

function getAuthToken(): string | null {
  return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
}

async function authorizedFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const token = getAuthToken();
  const headers = new Headers(init.headers || {});
  if (!headers.has('Content-Type') && init.method && init.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(url, { ...init, headers });
}

export const apiService = {
  async getScans(): Promise<ScanJob[]> {
    const response = await authorizedFetch(`${API_BASE}/scans/`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to fetch scans' }));
      throw new Error(errorData.error || 'Failed to fetch scans');
    }
    return response.json();
  },

  async createScan(target: string, profile: string = 'default'): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('🚀 Creating scan:', { target, profile });
    
    const response = await authorizedFetch(`${API_BASE}/scans/combined`, {
      method: 'POST',
      body: JSON.stringify({ target, profile }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to create scan' }));
      throw new Error(errorData.error || 'Failed to create scan');
    }
    
    const data = await response.json();
    console.log('✅ Scan created successfully:', data);
    return data;
  },

  async getScanJob(jobId: string): Promise<ScanJob> {
    const response = await authorizedFetch(`${API_BASE}/scans/scan-jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch scan job');
    return response.json();
  },

  async getScanResults(jobId: string): Promise<ScanResult[]> {
    const response = await authorizedFetch(`${API_BASE}/scans/scan-jobs/${jobId}/results`);
    if (!response.ok) throw new Error('Failed to fetch scan results');
    return response.json();
  },

  async retryScan(jobId: string): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('🔄 Retrying scan:', jobId);
    
    const response = await authorizedFetch(`${API_BASE}/scans/scan-jobs/${jobId}/retry`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to retry scan' }));
      throw new Error(errorData.error || 'Failed to retry scan');
    }
    
    const data = await response.json();
    console.log('✅ Scan retry successful, new job:', data);
    return data;
  },

  async cancelScan(jobId: string): Promise<{ success: boolean; job_id: string; status: string }> {
    const response = await authorizedFetch(`${API_BASE}/scans/scan-jobs/${jobId}/cancel`, {
      method: 'POST',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to cancel scan' }));
      throw new Error(errorData.error || 'Failed to cancel scan');
    }
    return response.json();
  },

  async getScanLogs(jobId: string): Promise<{ job_id: string; status: string; progress: number; log: string; error?: string }> {
    const response = await authorizedFetch(`${API_BASE}/scans/scan-jobs/${jobId}/logs`);
    if (!response.ok) throw new Error('Failed to fetch scan logs');
    return response.json();
  },

  // Web Scans
  async createWebScan(url: string, profile: string = 'web'): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('🌐 Creating web scan:', { url, profile });
    
    const response = await authorizedFetch(`${API_BASE}/scans/combined`, {
      method: 'POST',
      body: JSON.stringify({ target: url, profile }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to create web scan' }));
      throw new Error(errorData.error || 'Failed to create web scan');
    }
    
    const data = await response.json();
    console.log('✅ Web scan created successfully:', data);
    return data;
  },

  async getWebScanResults(jobId: string): Promise<WebScanResult[]> {
    const response = await authorizedFetch(`${API_BASE}/web-scans/results/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch web scan results');
    return response.json();
  },

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await authorizedFetch(`${API_BASE}/dashboard/stats`);
    if (!response.ok) throw new Error('Failed to fetch dashboard stats');
    return response.json();
  },

  async getScanInsights(jobId: string): Promise<any> {
    const response = await authorizedFetch(`${API_BASE}/insights/scan/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch scan insights');
    return response.json();
  },

  async getAssets(): Promise<any[]> {
    const response = await authorizedFetch(`${API_BASE}/advanced/assets`);
    if (!response.ok) throw new Error('Failed to fetch assets');
    return response.json();
  },

  async createEnhancedScan(target: string, scanType: string): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('⚡ Creating enhanced scan:', { target, scanType });
    
    const response = await authorizedFetch(`${API_BASE}/enhanced/scan`, {
      method: 'POST',
      body: JSON.stringify({ target, scan_type: scanType }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to create enhanced scan' }));
      throw new Error(errorData.error || 'Failed to create enhanced scan');
    }
    
    const data = await response.json();
    console.log('✅ Enhanced scan created successfully:', data);
    return data;
  },

  async getEnhancedScanResults(jobId: string): Promise<any> {
    const response = await authorizedFetch(`${API_BASE}/enhanced/technologies/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch enhanced scan results');
    return response.json();
  },

  async listPlaybooks(): Promise<any[]> {
    const response = await authorizedFetch(`${API_BASE}/automation/playbooks`);
    if (!response.ok) throw new Error('Failed to list playbooks');
    return response.json();
  },

  async createPlaybook(payload: {
    name: string;
    target: string;
    profile?: string;
    schedule_minutes?: number;
    enabled?: boolean;
    tags?: Record<string, any>;
  }): Promise<any> {
    const response = await authorizedFetch(`${API_BASE}/automation/playbooks`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to create playbook' }));
      throw new Error(errorData.error || 'Failed to create playbook');
    }
    return response.json();
  },

  async runPlaybook(playbookId: string): Promise<{ playbook_id: string; job_id: string }> {
    const response = await authorizedFetch(`${API_BASE}/automation/playbooks/${playbookId}/run`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to run playbook');
    return response.json();
  },

  async runDuePlaybooks(limit = 20): Promise<{ created: Array<{ playbook_id: string; job_id: string }>; count: number }> {
    const response = await authorizedFetch(`${API_BASE}/automation/run-due?limit=${limit}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to run due playbooks');
    return response.json();
  },

  async getJobArtifact(jobId: string): Promise<any> {
    const response = await authorizedFetch(`${API_BASE}/automation/reports/job/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch job artifact');
    return response.json();
  },

  async createDiffReport(oldJobId: string, newJobId: string): Promise<any> {
    const response = await authorizedFetch(`${API_BASE}/automation/reports/diff`, {
      method: 'POST',
      body: JSON.stringify({ old_job_id: oldJobId, new_job_id: newJobId }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to create diff report' }));
      throw new Error(errorData.error || 'Failed to create diff report');
    }
    return response.json();
  },

  async listDiffReports(limit = 100): Promise<any[]> {
    const response = await authorizedFetch(`${API_BASE}/automation/reports/diff?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to list diff reports');
    return response.json();
  },
};
