import React, { useState } from 'react';
import { VulnerabilityScanRequest } from '../../services/vulnerabilityApi';

interface NewScanModalProps {
  onStartScan: (config: VulnerabilityScanRequest) => void;
}

const NewScanModal: React.FC<NewScanModalProps> = ({ onStartScan }) => {
  const [scanConfig, setScanConfig] = useState<VulnerabilityScanRequest>({
    target: '',
    assessment_type: 'full',
    aggressive: false,
    web_scan_config: {
      directory_enum: true,
      header_analysis: true,
      ssl_analysis: true
    },
    ssl_config: {
      check_protocols: true,
      check_ciphers: true,
      check_certificate: true
    },
    cve_config: {
      check_known_vulnerabilities: true,
      version_detection: true
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStartScan(scanConfig);
    (document.getElementById('new_scan_modal') as HTMLDialogElement)?.close();
  };

  return (
    <dialog id="new_scan_modal" className="modal">
      <div className="modal-box w-11/12 max-w-5xl">
        <h3 className="font-bold text-lg mb-4">New Vulnerability Assessment</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text">Target</span>
            </label>
            <input
              type="text"
              placeholder="https://example.com or 192.168.1.1"
              className="input input-bordered"
              value={scanConfig.target}
              onChange={(e) => setScanConfig({...scanConfig, target: e.target.value})}
              required
            />
          </div>

          <div className="form-control">
            <label className="label">
              <span className="label-text">Assessment Type</span>
            </label>
            <select
              className="select select-bordered"
              value={scanConfig.assessment_type}
              onChange={(e) => setScanConfig({...scanConfig, assessment_type: e.target.value as any})}
            >
              <option value="full">Full Assessment</option>
              <option value="web_security">Web Security Only</option>
              <option value="ssl_analysis">SSL Analysis</option>
              <option value="cve_scan">CVE Scan</option>
              <option value="credential_testing">Credential Testing</option>
            </select>
          </div>

          <div className="form-control">
            <label className="cursor-pointer label">
              <span className="label-text">Aggressive Mode</span>
              <input
                type="checkbox"
                className="toggle toggle-primary"
                checked={scanConfig.aggressive}
                onChange={(e) => setScanConfig({...scanConfig, aggressive: e.target.checked})}
              />
            </label>
          </div>

          {/* Web Scan Config */}
          {['full', 'web_security'].includes(scanConfig.assessment_type) && (
            <div className="border rounded-lg p-4">
              <h4 className="font-semibold mb-2">Web Security Options</h4>
              <div className="space-y-2">
                {Object.entries(scanConfig.web_scan_config || {}).map(([key, value]) => (
                  <label key={key} className="cursor-pointer label justify-start">
                    <input
                      type="checkbox"
                      className="checkbox checkbox-primary mr-2"
                      checked={value as boolean}
                      onChange={(e) => setScanConfig({
                        ...scanConfig,
                        web_scan_config: {
                          ...scanConfig.web_scan_config,
                          [key]: e.target.checked
                        }
                      })}
                    />
                    <span className="label-text capitalize">{key.replace(/_/g, ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="modal-action">
            <button type="submit" className="btn btn-primary">Start Scan</button>
            <button 
              type="button" 
              className="btn"
              onClick={() => (document.getElementById('new_scan_modal') as HTMLDialogElement)?.close()}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
};

export default NewScanModal;