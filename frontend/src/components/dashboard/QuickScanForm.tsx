import React, { useState } from 'react';
import { X, Globe, Server } from 'lucide-react';

interface QuickScanFormProps {
  onSubmit: (target: string, profile: string) => void;
  onCancel: () => void;
}

const QuickScanForm: React.FC<QuickScanFormProps> = ({ onSubmit, onCancel }) => {
  const [target, setTarget] = useState('');
  const [profile, setProfile] = useState('default');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim()) return;

    setIsSubmitting(true);
    try {
      await onSubmit(target.trim(), profile);
    } finally {
      setIsSubmitting(false);
    }
  };

  const scanExamples = [
    { target: 'scanme.nmap.org', profile: 'default', description: 'NMAP Test Server' },
    { target: 'google.com', profile: 'web', description: 'Web Security Scan' },
    { target: 'localhost', profile: 'default', description: 'Local Machine' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-xl border border-gray-700 w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-gray-200">Start New Scan</h3>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
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

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Scan Type
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setProfile('default')}
                  className={`p-3 border rounded-lg text-left transition-colors ${
                    profile === 'default'
                      ? 'border-blue-500 bg-blue-900/20 text-blue-400'
                      : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500'
                  }`}
                >
                  <Server className="w-5 h-5 mb-1" />
                  <div className="text-sm font-medium">Network Scan</div>
                  <div className="text-xs text-gray-400">IPs & Ports</div>
                </button>
                
                <button
                  type="button"
                  onClick={() => setProfile('web')}
                  className={`p-3 border rounded-lg text-left transition-colors ${
                    profile === 'web'
                      ? 'border-purple-500 bg-purple-900/20 text-purple-400'
                      : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500'
                  }`}
                >
                  <Globe className="w-5 h-5 mb-1" />
                  <div className="text-sm font-medium">Web Scan</div>
                  <div className="text-xs text-gray-400">Websites & Apps</div>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Quick Examples
              </label>
              <div className="space-y-2">
                {scanExamples.map((example, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => {
                      setTarget(example.target);
                      setProfile(example.profile);
                    }}
                    className="w-full text-left p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 transition-colors"
                  >
                    <span className="font-mono">{example.target}</span>
                    <span className="text-gray-500 text-xs ml-2">({example.description})</span>
                  </button>
                ))}
              </div>
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
              disabled={!target.trim() || isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Starting...' : 'Start Scan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default QuickScanForm;