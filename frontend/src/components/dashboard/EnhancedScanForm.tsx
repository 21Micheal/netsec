import React, { useState } from 'react';
import { Zap, Server, Globe, Cpu, X } from 'lucide-react';

interface EnhancedScanFormProps {
  onSubmit: (target: string, scanType: string) => void;
  onCancel: () => void;
}

const EnhancedScanForm: React.FC<EnhancedScanFormProps> = ({ onSubmit, onCancel }) => {
  const [target, setTarget] = useState('');
  const [scanType, setScanType] = useState('comprehensive');

  const scanTypes = [
    {
      id: 'comprehensive',
      name: 'Comprehensive Scan',
      description: 'Full service enumeration, OS detection, and technology fingerprinting',
      icon: Cpu,
      color: 'text-purple-400'
    },
    {
      id: 'web_enhanced',
      name: 'Web Technology Scan',
      description: 'Advanced web technology detection and security header analysis',
      icon: Globe,
      color: 'text-green-400'
    },
    {
      id: 'service_detection',
      name: 'Service Enumeration',
      description: 'Detailed service version detection and vulnerability indicators',
      icon: Server,
      color: 'text-blue-400'
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim()) return;
    onSubmit(target.trim(), scanType);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-xl border border-gray-700 w-full max-w-2xl">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <Zap className="w-6 h-6 text-yellow-400" />
            <h3 className="text-lg font-semibold text-gray-200">Enhanced Security Scan</h3>
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-6">
            {/* Target Input */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Scan Target
              </label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="IP address, domain, or URL"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                required
              />
            </div>

            {/* Scan Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-3">
                Scan Type
              </label>
              <div className="grid grid-cols-1 gap-3">
                {scanTypes.map((type) => (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setScanType(type.id)}
                    className={`p-4 border rounded-lg text-left transition-colors ${
                      scanType === type.id
                        ? 'border-purple-500 bg-purple-900/20 text-purple-400'
                        : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <type.icon className={`w-5 h-5 mt-0.5 ${type.color}`} />
                      <div className="flex-1">
                        <div className="font-medium">{type.name}</div>
                        <div className="text-sm text-gray-400 mt-1">{type.description}</div>
                      </div>
                      {scanType === type.id && (
                        <div className="w-2 h-2 bg-purple-400 rounded-full mt-2" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Scan Details */}
            <div className="bg-gray-700/50 rounded-lg p-4">
              <h4 className="font-medium text-gray-200 mb-2">What this scan will do:</h4>
              <ul className="text-sm text-gray-400 space-y-1">
                {scanType === 'comprehensive' && (
                  <>
                    <li>• Full port scanning with service detection</li>
                    <li>• OS fingerprinting and technology stack analysis</li>
                    <li>• Vulnerability indicator checking</li>
                    <li>• Security header analysis (for web services)</li>
                  </>
                )}
                {scanType === 'web_enhanced' && (
                  <>
                    <li>• Web technology framework detection</li>
                    <li>• Security header analysis and scoring</li>
                    <li>• SSL/TLS certificate inspection</li>
                    <li>• Common web vulnerability checks</li>
                  </>
                )}
                {scanType === 'service_detection' && (
                  <>
                    <li>• Detailed service version detection</li>
                    <li>• Technology stack identification</li>
                    <li>• Outdated software version checking</li>
                    <li>• Common misconfiguration detection</li>
                  </>
                )}
              </ul>
            </div>
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:border-gray-500 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!target.trim()}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Start Enhanced Scan
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EnhancedScanForm;