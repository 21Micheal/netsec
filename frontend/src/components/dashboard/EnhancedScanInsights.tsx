import React from 'react';
import { Server, Globe, Cpu, Shield, AlertTriangle, CheckCircle } from 'lucide-react';

interface EnhancedScanInsightsProps {
  insights: any;
}

const EnhancedScanInsights: React.FC<EnhancedScanInsightsProps> = ({ insights }) => {
  if (!insights) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="text-center text-gray-400">
          <Cpu className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No enhanced scan insights available</p>
        </div>
      </div>
    );
  }

  const { technologies, services, web_technologies, vulnerability_indicators, summary } = insights;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Services Found</p>
              <p className="text-2xl font-bold text-blue-400">{summary?.services_detected || 0}</p>
            </div>
            <Server className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Technologies</p>
              <p className="text-2xl font-bold text-purple-400">{summary?.technologies_found || 0}</p>
            </div>
            <Cpu className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Vulnerability Indicators</p>
              <p className="text-2xl font-bold text-orange-400">{summary?.vulnerabilities_found || 0}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-400" />
          </div>
        </div>

        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Hosts Scanned</p>
              <p className="text-2xl font-bold text-green-400">{summary?.total_hosts || 0}</p>
            </div>
            <Globe className="w-8 h-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* Detected Technologies */}
      {technologies && technologies.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 flex items-center">
              <Cpu className="w-5 h-5 mr-2 text-purple-400" />
              Detected Technologies
            </h3>
          </div>
          <div className="p-4">
            <div className="flex flex-wrap gap-2">
              {Array.from(new Set(technologies as string[])).map((tech: string, index: number) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-purple-900 text-purple-300 rounded-full text-sm font-medium"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Web Technologies */}
      {web_technologies && web_technologies.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 flex items-center">
              <Globe className="w-5 h-5 mr-2 text-green-400" />
              Web Technologies
            </h3>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {web_technologies.map((tech: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
                  <div>
                    <p className="font-medium text-gray-200">{tech.name}</p>
                    <p className="text-sm text-gray-400">
                      {tech.category} • Confidence: {tech.confidence}%
                    </p>
                    {tech.evidence && tech.evidence.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">
                        Evidence: {tech.evidence[0]}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="w-16 bg-gray-600 rounded-full h-2">
                      <div
                        className="h-2 bg-green-500 rounded-full"
                        style={{ width: `${tech.confidence}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-400">{tech.confidence}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {insights.scan_duration && (
        <div className="text-xs text-gray-500 mt-2">
          Scan completed in {(insights.scan_duration / 60).toFixed(1)} minutes
        </div>
      )}

        {insights.warning && (
        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 text-yellow-400">
                <AlertTriangle className="w-5 h-5" />
                <div>
                    <p className="font-medium">Limited Scan Results</p>
                    <p className="text-sm text-yellow-300">{insights.warning}</p>
                    <p className="text-xs text-yellow-500 mt-1">
                        Some advanced features like OS detection require root privileges.
                    </p>
                </div>
            </div>
        </div>
    )}

      {/* Services with Technologies */}
      {services && services.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 flex items-center">
              <Server className="w-5 h-5 mr-2 text-blue-400" />
              Services with Technologies
            </h3>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {services.map((service: any, index: number) => (
                <div key={index} className="p-3 bg-gray-700/50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <span className="font-mono text-blue-400 bg-blue-900/20 px-2 py-1 rounded text-sm">
                        {service.port}/{service.protocol}
                      </span>
                      <span className="font-medium text-gray-200">{service.base_service}</span>
                      {service.product && (
                        <span className="text-sm text-gray-400">{service.product} {service.version}</span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">Confidence: {service.confidence}</span>
                  </div>
                  
                  {service.technologies && service.technologies.length > 0 && (
                    <div className="mt-2">
                      <span className="text-xs text-gray-400 mr-2">Technologies:</span>
                      {service.technologies.map((tech: string, techIndex: number) => (
                        <span
                          key={techIndex}
                          className="inline-block px-2 py-1 bg-gray-600 text-gray-300 rounded text-xs mr-1 mb-1"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedScanInsights;