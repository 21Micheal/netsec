import React from 'react';
import { Shield, AlertTriangle, CheckCircle, Globe, Lock, Cookie } from 'lucide-react';

interface WebScanInsightsProps {
  insights: any;
}

const WebScanInsights: React.FC<WebScanInsightsProps> = ({ insights }) => {
  if (!insights || !insights.web_results) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="text-center text-gray-400">
          <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No web scan insights available</p>
        </div>
      </div>
    );
  }

  const { web_results, security_indicators, summary } = insights;
  const { headers, cookies, issues } = web_results;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">HTTP Status</p>
              <p className={`text-2xl font-bold ${
                web_results.http_status === 200 ? 'text-green-400' : 
                web_results.http_status >= 400 ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {web_results.http_status}
              </p>
            </div>
            <Globe className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Security Headers</p>
              <p className="text-2xl font-bold text-green-400">
                {Object.keys(headers || {}).length}
              </p>
            </div>
            <Shield className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Cookies</p>
              <p className="text-2xl font-bold text-yellow-400">
                {Object.keys(cookies || {}).length}
              </p>
            </div>
            <Cookie className="w-8 h-8 text-yellow-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Security Issues</p>
              <p className="text-2xl font-bold text-orange-400">
                {security_indicators?.length || 0}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-400" />
          </div>
        </div>
      </div>

      {/* Response Details */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-gray-200">Response Details</h3>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-200 mb-2">URL</h4>
              <p className="text-sm text-gray-400 break-all">{web_results.url}</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-200 mb-2">Final URL</h4>
              <p className="text-sm text-gray-400 break-all">{web_results.final_url || web_results.url}</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-200 mb-2">Response Time</h4>
              <p className="text-sm text-gray-400">
                {web_results.response_time ? `${(web_results.response_time * 1000).toFixed(0)} ms` : 'N/A'}
              </p>
            </div>
            <div>
              <h4 className="font-medium text-gray-200 mb-2">Content Length</h4>
              <p className="text-sm text-gray-400">
                {web_results.content_length ? `${web_results.content_length} bytes` : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Security Headers */}
      {headers && Object.keys(headers).length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200">Security Headers</h3>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              {Object.entries(headers).map(([key, value]) => (
                <div key={key} className="flex justify-between items-start p-3 bg-gray-700/50 rounded">
                  <div>
                    <p className="font-medium text-gray-200">{key}</p>
                    <p className="text-sm text-gray-400 break-all">{String(value)}</p>
                  </div>
                  <Lock className="w-4 h-4 text-green-400 mt-1" />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Security Findings */}
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
                      {indicator.recommendation && (
                        <p className="text-sm text-blue-400 mt-1">Recommendation: {indicator.recommendation}</p>
                      )}
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

export default WebScanInsights;