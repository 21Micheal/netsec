import React from 'react';
import { AlertTriangle, Shield, TrendingUp, Globe } from 'lucide-react';

interface RiskDashboardProps {
  assets: any[];
  vulnerabilities: any[];
  recentScans: any[];
}

const RiskDashboard: React.FC<RiskDashboardProps> = ({ assets, vulnerabilities, recentScans }) => {
  const criticalAssets = assets.filter(a => a.risk_score >= 80);
  const highVulnerabilities = vulnerabilities.filter(v => v.severity === 'CRITICAL' || v.severity === 'HIGH');
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
      {/* Risk Overview Cards */}
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-400 text-sm">Critical Assets</p>
            <p className="text-2xl font-bold text-red-400">{criticalAssets.length}</p>
          </div>
          <AlertTriangle className="w-8 h-8 text-red-400" />
        </div>
      </div>
      
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-400 text-sm">High Risk Vulns</p>
            <p className="text-2xl font-bold text-orange-400">{highVulnerabilities.length}</p>
          </div>
          <Shield className="w-8 h-8 text-orange-400" />
        </div>
      </div>
      
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-400 text-sm">Total Assets</p>
            <p className="text-2xl font-bold text-blue-400">{assets.length}</p>
          </div>
          <Globe className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-400 text-sm">Avg Risk Score</p>
            <p className="text-2xl font-bold text-yellow-400">
              {assets.length ? Math.round(assets.reduce((acc, a) => acc + a.risk_score, 0) / assets.length) : 0}
            </p>
          </div>
          <TrendingUp className="w-8 h-8 text-yellow-400" />
        </div>
      </div>
    </div>
  );
};

export default RiskDashboard;