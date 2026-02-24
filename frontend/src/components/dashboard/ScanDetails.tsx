// components/vulnerability/ScanDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import VulnerabilityApi from '../../services/vulnerabilityApi';
import { ScanJob } from '../../types/vulnerability';
import ScanResults from '../vulnerability/ScanResults';

const ScanDetail: React.FC = () => {
  const { scanId } = useParams<{ scanId: string }>();
  const [scan, setScan] = useState<ScanJob | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadScanDetail = async () => {
      if (!scanId) return;
      
      try {
        setIsLoading(true);
        const scanData = await VulnerabilityApi.getScanStatus(scanId);
        setScan(scanData);
      } catch (err) {
        setError('Failed to load scan details');
        console.error('Error loading scan:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadScanDetail();
  }, [scanId]);

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">Loading scan details...</div>;
  }

  if (error) {
    return <div className="alert alert-error">{error}</div>;
  }

  if (!scan) {
    return <div className="alert alert-warning">Scan not found</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="card bg-base-100 shadow">
        <div className="card-body">
          <h1 className="card-title">Scan Details</h1>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <strong>Target:</strong> {scan.target}
            </div>
            <div>
              <strong>Type:</strong> {scan.scan_type}
            </div>
            <div>
              <strong>Status:</strong> 
              <span className={`badge ml-2 ${
                scan.status === 'running' ? 'badge-primary' :
                scan.status === 'finished' ? 'badge-success' :
                scan.status === 'failed' ? 'badge-error' : 'badge-secondary'
              }`}>
                {scan.status}
              </span>
            </div>
            <div>
              <strong>Started:</strong> {new Date(scan.created_at).toLocaleString()}
            </div>
            {scan.finished_at && (
              <div>
                <strong>Completed:</strong> {new Date(scan.finished_at).toLocaleString()}
              </div>
            )}
            {scan.duration && (
              <div>
                <strong>Duration:</strong> {scan.duration.toFixed(2)}s
              </div>
            )}
          </div>
        </div>
      </div>

      {scan.vulnerability_results ? (
        <ScanResults scan={scan} />
      ) : (
        <div className="alert alert-info">
          <span>No scan results available. Scan status: {scan.status}</span>
        </div>
      )}
    </div>
  );
};

export default ScanDetail;