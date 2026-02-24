import React from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, Network } from 'lucide-react';
import WebScanInsights from './WebScanInsights';
// Add import for EnhancedScanInsights
import EnhancedScanInsights from './EnhancedScanInsights';

interface ScanInsightsProps {
  jobId: string;
  insights: any;
}

const ScanInsights: React.FC<ScanInsightsProps> = ({ jobId, insights }) => {
  // Check if this is an enhanced scan
  const isEnhancedScan = insights?.scan_type?.includes('enhanced') || 
                         insights?.technologies?.length > 0 ||
                         insights?.web_technologies?.length > 0;
  
  if (isEnhancedScan) {
    return <EnhancedScanInsights insights={insights} />;
  }

  // Check if this is a web scan
  const isWebScan = insights?.web_results !== undefined;
  if (isWebScan) {
    return <WebScanInsights insights={insights} />;
  }
  
  else if (!insights || Object.keys(insights).length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="text-center text-gray-400">
          <Network className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No insights available for this scan</p>
          <p className="text-sm">Scan results are being processed...</p>
        </div>
      </div>
    );
  }

  const { open_ports, services, security_indicators, summary } = insights;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Open Ports</p>
              <p className="text-2xl font-bold text-blue-400">{summary?.total_open_ports || 0}</p>
            </div>
            <Network className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Services</p>
              <p className="text-2xl font-bold text-green-400">{services?.length || 0}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Security Findings</p>
              <p className="text-2xl font-bold text-orange-400">{security_indicators?.length || 0}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Risk Level</p>
              <p className={`text-2xl font-bold ${
                summary?.risk_level === 'HIGH' ? 'text-red-400' :
                summary?.risk_level === 'MEDIUM' ? 'text-orange-400' :
                'text-green-400'
              }`}>
                {summary?.risk_level || 'LOW'}
              </p>
            </div>
            <Shield className="w-8 h-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Open Ports */}
      {open_ports && open_ports.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200">Open Ports</h3>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              {open_ports.map((port: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 text-center">
                      <span className="font-mono text-blue-400">{port.port}/{port.protocol}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-200">{port.service}</p>
                      {port.version && (
                        <p className="text-sm text-gray-400">{port.version}</p>
                      )}
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    port.state === 'open' ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-300'
                  }`}>
                    {port.state}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Security Indicators */}
      {security_indicators && security_indicators.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200">Security Findings</h3>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {security_indicators.map((indicator: any, index: number) => (
                <div key={index} className={`p-3 rounded border-l-4 ${
                  indicator.severity === 'HIGH' ? 'border-red-500 bg-red-900/20' :
                  indicator.severity === 'MEDIUM' ? 'border-orange-500 bg-orange-900/20' :
                  'border-yellow-500 bg-yellow-900/20'
                }`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-200">{indicator.message}</p>
                      <p className="text-sm text-gray-400 mt-1">Type: {indicator.type}</p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      indicator.severity === 'HIGH' ? 'bg-red-900 text-red-300' :
                      indicator.severity === 'MEDIUM' ? 'bg-orange-900 text-orange-300' :
                      'bg-yellow-900 text-yellow-300'
                    }`}>
                      {indicator.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanInsights;