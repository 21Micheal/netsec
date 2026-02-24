import { ScanJob, ScanResult, WebScanResult, DashboardStats } from '../types';

const API_BASE = 'http://localhost:5000/api';

export const apiService = {
  async getScans(): Promise<ScanJob[]> {
    const response = await fetch(`${API_BASE}/scans/`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to fetch scans' }));
      throw new Error(errorData.error || 'Failed to fetch scans');
    }
    return response.json();
  },

  async createScan(target: string, profile: string = 'default'): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('🚀 Creating scan:', { target, profile });
    
    const response = await fetch(`${API_BASE}/scans/combined`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    const response = await fetch(`${API_BASE}/scans/scan-jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch scan job');
    return response.json();
  },

  async getScanResults(jobId: string): Promise<ScanResult[]> {
    const response = await fetch(`${API_BASE}/scans/scan-jobs/${jobId}/results`);
    if (!response.ok) throw new Error('Failed to fetch scan results');
    return response.json();
  },

  async retryScan(jobId: string): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('🔄 Retrying scan:', jobId);
    
    const response = await fetch(`${API_BASE}/scans/scan-jobs/${jobId}/retry`, {
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

  // Web Scans
  async createWebScan(url: string, profile: string = 'web'): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('🌐 Creating web scan:', { url, profile });
    
    const response = await fetch(`${API_BASE}/scans/combined`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    const response = await fetch(`${API_BASE}/web-scans/results/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch web scan results');
    return response.json();
  },

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await fetch(`${API_BASE}/dashboard/stats`);
    if (!response.ok) throw new Error('Failed to fetch dashboard stats');
    return response.json();
  },

  async getScanInsights(jobId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/insights/scan/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch scan insights');
    return response.json();
  },

  async getAssets(): Promise<any[]> {
    const response = await fetch(`${API_BASE}/advanced/assets`);
    if (!response.ok) throw new Error('Failed to fetch assets');
    return response.json();
  },

  async createEnhancedScan(target: string, scanType: string): Promise<{ success: boolean; job_id: string; message: string }> {
    console.log('⚡ Creating enhanced scan:', { target, scanType });
    
    const response = await fetch(`${API_BASE}/enhanced/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    const response = await fetch(`${API_BASE}/enhanced/technologies/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch enhanced scan results');
    return response.json();
  }
};
