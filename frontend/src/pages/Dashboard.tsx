import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Activity,
  Globe,
  Shield,
  Cpu,
  Play,
  RefreshCcw,
  AlertTriangle,
  Server,
  Network,
  Eye,
  BarChart3,
  Zap
} from 'lucide-react';
import { useSocket } from '../hooks/useSocket';
import { apiService } from '../services/api';
import ScanInsights from '../components/dashboard/ScanInsights';
import RiskDashboard from '../components/dashboard/RiskDashboard';
import QuickScanForm from '../components/dashboard/QuickScanForm';
import EnhancedScanForm from '../components/dashboard/EnhancedScanForm';
import { ScanJob, DashboardStats } from '../types';

const Dashboard: React.FC = () => {
  const [scans, setScans] = useState<ScanJob[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    activeScans: 0,
    completedJobs: 0,
    systemLoad: 0,
    alerts: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedScan, setSelectedScan] = useState<ScanJob | null>(null);
  const [scanInsights, setScanInsights] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'scans' | 'insights'>('overview');
  const [showScanForm, setShowScanForm] = useState(false);
  const [showEnhancedForm, setShowEnhancedForm] = useState(false);
  

  const { lastMessage, isConnected, subscribeToJob, unsubscribeFromJob, debugSubscriptions } = useSocket();

  // Add debug button to your header
  <button
    onClick={debugSubscriptions}
    className="text-xs text-gray-500 hover:text-gray-400"
    title="Debug Subscriptions"
  >
    🐛
  </button>
  
  // Refs to track state without causing re-renders
  const scansRef = useRef<ScanJob[]>([]);
  const selectedScanRef = useRef<ScanJob | null>(null);
  const subscribedJobsRef = useRef<Set<string>>(new Set());
  const lastProcessedMessage = useRef<string>(''); // Track last processed message

  // Update refs when state changes
  useEffect(() => {
    scansRef.current = scans;
  }, [scans]);

  useEffect(() => {
    selectedScanRef.current = selectedScan;
  }, [selectedScan]);

  // Fetch all scans and stats
  // In your fetchDashboardData function
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [scansData, statsData] = await Promise.all([
        apiService.getScans(),
        apiService.getDashboardStats()
      ]);
      
      console.log('📊 Raw scans data from API:', scansData);
      console.log('📈 Raw stats data from API:', statsData);
      
      // Log scan types for debugging
      const scanTypes = scansData.reduce((acc: any, scan: any) => {
        acc[scan.type] = (acc[scan.type] || 0) + 1;
        return acc;
      }, {});
      console.log('🔍 Scan type distribution:', scanTypes);
      
      setScans(scansData);
      setStats(statsData);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch insights for a specific scan
  const fetchScanInsights = async (jobId: string) => {
    try {
      const data = await apiService.getScanInsights(jobId);
      setScanInsights(data);
      setSelectedScan(scansRef.current.find(scan => scan.id === jobId) || null);
      setActiveTab('insights');
    } catch (err: any) {
      console.error('Error fetching scan insights:', err);
      setError(err.message);
    }
  };

  // Handle new scan creation
  const handleNewScan = async (target: string, profile: string) => {
    try {
      await apiService.createScan(target, profile);
      setShowScanForm(false);
      // Small delay to allow backend to process
      setTimeout(() => {
        fetchDashboardData();
      }, 1000);
    } catch (err: any) {
      console.error('Error creating scan:', err);
      setError(err.message);
    }
  };

    // Handle enhanced scans
  const handleEnhancedScan = async (target: string, scanType: string) => {
    try {
      await apiService.createEnhancedScan(target, scanType);
      setShowEnhancedForm(false);
      // Small delay to allow backend to process
      setTimeout(() => {
        fetchDashboardData();
      }, 1000);
    } catch (err: any) {
      setError(err.message);
    }
  };

  // **FIXED: Improved WebSocket message handling**
// **FIXED: Improved WebSocket message handling**
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'scan_update') return;

    const { job_id, status, progress } = lastMessage.data;
    
    // Create a unique identifier WITHOUT timestamp for proper duplicate detection
    const messageId = `${job_id}-${status}-${progress}`;
    
    // Skip if we just processed this exact same update
    if (lastProcessedMessage.current === messageId) {
      console.log('🔄 Skipping duplicate message:', messageId);
      return;
    }
    
    lastProcessedMessage.current = messageId;
    
    console.log(`📡 Processing WebSocket update for ${job_id}:`, { status, progress });
    
    // Validate message data
    if (!job_id || typeof job_id !== 'string') {
      console.log('🔄 Ignoring update without valid job_id');
      return;
    }

    // **FIXED: Use functional update to ensure we have latest state**
    setScans(prevScans => {
      const scanExists = prevScans.some(scan => scan.id === job_id);
      
      if (!scanExists) {
        console.log(`🆕 Adding new scan to state: ${job_id}`);
        // This is a new scan, add it to the list
        const newScan: ScanJob = {
          id: job_id,
          target: lastMessage.data.target || 'Unknown target',
          profile: lastMessage.data.profile || 'default',
          status: status,
          progress: progress,
          createdAt: new Date().toISOString(),
          finishedAt: status === 'finished' || status === 'failed' ? new Date().toISOString() : undefined,
          type: lastMessage.data.profile === 'web' ? 'web' : 'network'
        };
        return [newScan, ...prevScans];
      } else {
        // Update existing scan
        const updatedScans = prevScans.map(scan => 
          scan.id === job_id 
            ? { 
                ...scan, 
                status, 
                progress,
                finishedAt: (status === 'finished' || status === 'failed') 
                  ? (scan.finishedAt || new Date().toISOString())
                  : scan.finishedAt
              }
            : scan
        );
        
        console.log(`🔄 Updated scan ${job_id}: ${status} (${progress}%)`);
        return updatedScans;
      }
    });

    // Handle completion/failure - refresh stats immediately
    if (status === 'finished' || status === 'failed') {
      console.log(`🎉 Scan ${job_id} completed with status: ${status}`);
      
      // Refresh insights if this is the selected scan
      const currentSelectedScan = selectedScanRef.current;
      if (currentSelectedScan?.id === job_id) {
        console.log(`🔍 Refreshing insights for selected scan: ${job_id}`);
        setTimeout(() => fetchScanInsights(job_id), 500);
      }
      
      // Refresh dashboard stats after completion
      setTimeout(() => {
        console.log(`📈 Refreshing dashboard stats after scan completion`);
        fetchDashboardData();
      }, 1000);
    }
  }, [lastMessage, fetchDashboardData, fetchScanInsights]); // Added missing dependencies


  // **FIXED: Improved subscription management**
  useEffect(() => {
    const currentScans = scansRef.current;
    const currentlySubscribed = subscribedJobsRef.current;

    // Subscribe to active scans
    currentScans.forEach(scan => {
      if ((scan.status === 'running' || scan.status === 'queued') && !currentlySubscribed.has(scan.id)) {
        console.log(`🔔 Subscribing to job: ${scan.id}`);
        subscribeToJob(scan.id);
        currentlySubscribed.add(scan.id);
      }
    });

    // Unsubscribe from completed/failed scans
    currentlySubscribed.forEach(jobId => {
      const scan = currentScans.find(s => s.id === jobId);
      if (!scan || (scan.status !== 'running' && scan.status !== 'queued')) {
        console.log(`🔕 Unsubscribing from job: ${jobId}`);
        unsubscribeFromJob(jobId);
        currentlySubscribed.delete(jobId);
      }
    });

  }, [scans, subscribeToJob, unsubscribeFromJob]); // Only depend on scans array changes

  // **FIXED: Cleanup subscriptions on unmount**
  useEffect(() => {
    return () => {
      console.log('🧹 Cleaning up all WebSocket subscriptions');
      subscribedJobsRef.current.forEach(jobId => {
        unsubscribeFromJob(jobId);
      });
      subscribedJobsRef.current.clear();
    };
  }, [unsubscribeFromJob]);

  // Initial data load
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Stats configuration
  const statsConfig = [
    {
      title: "Active Scans",
      value: stats.activeScans.toString(),
      icon: Activity,
      color: "text-blue-400",
      bgColor: "bg-blue-500",
      description: "Currently running scans"
    },
    {
      title: "Completed Jobs",
      value: stats.completedJobs.toString(),
      icon: Shield,
      color: "text-green-400",
      bgColor: "bg-green-500",
      description: "Successfully finished scans"
    },
    {
      title: "System Load",
      value: `${stats.systemLoad}%`,
      icon: Cpu,
      color: "text-yellow-400",
      bgColor: "bg-yellow-500",
      description: "Current system utilization"
    },
    {
      title: "Security Alerts",
      value: stats.alerts.toString(),
      icon: AlertTriangle,
      color: "text-red-400",
      bgColor: "bg-red-500",
      description: "Critical security findings"
    }
  ];

  // **ADD: Debug function to check current state**
  const debugState = () => {
    console.log('=== DASHBOARD DEBUG ===');
    console.log('Scans:', scans.length);
    console.log('Subscribed jobs:', Array.from(subscribedJobsRef.current));
    console.log('Selected scan:', selectedScan?.id);
    console.log('WebSocket connected:', isConnected);
    console.log('=======================');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Security Dashboard</h1>
                <p className="text-gray-400 text-sm">Network & Web Security Monitoring</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Debug button - remove in production */}
              <button
                onClick={debugState}
                className="text-xs text-gray-500 hover:text-gray-400"
                title="Debug State"
              >
                🐛
              </button>
              
              <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                isConnected ? 'bg-green-900/20 text-green-400' : 'bg-red-900/20 text-red-400'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-sm">WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</span>
              </div>
              
              {/* Enhanced Scan Button */}
              <button
                onClick={() => setShowEnhancedForm(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <Zap className="w-4 h-4" />
                <span>Enhanced Scan</span>
              </button>
              
              {/* Quick Scan Button */}
              <button
                onClick={() => setShowScanForm(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <Play className="w-4 h-4" />
                <span>Quick Scan</span>
              </button>
              
              <button
                onClick={fetchDashboardData}
                disabled={loading}
                className="flex items-center space-x-2 px-4 py-2 border border-gray-600 hover:border-gray-500 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Scan Modal */}
      {showScanForm && (
        <QuickScanForm
          onSubmit={handleNewScan}
          onCancel={() => setShowScanForm(false)}
        />
      )}

      {showEnhancedForm && (
        <EnhancedScanForm
          onSubmit={handleEnhancedScan}
          onCancel={() => setShowEnhancedForm(false)}
        />
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-700 rounded-lg text-red-400">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5" />
              <span>Error: {error}</span>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="mb-8 border-b border-gray-700">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: BarChart3 },
              { id: 'scans', name: 'Recent Scans', icon: Activity },
              { id: 'insights', name: 'Scan Insights', icon: Eye },             
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              {statsConfig.map((stat) => (
                <div
                  key={stat.title}
                  className="bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-600 transition-colors p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm text-gray-400">{stat.title}</p>
                      <p className="text-3xl font-bold text-gray-100">{stat.value}</p>
                      <p className="text-xs text-gray-500 mt-1">{stat.description}</p>
                    </div>
                    <stat.icon className={`w-8 h-8 ${stat.color}`} />
                  </div>
                  <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${stat.bgColor}`}
                      style={{
                        width: stat.title === 'System Load' 
                          ? `${stats.systemLoad}%`
                          : stat.title === 'Active Scans'
                          ? `${Math.min(100, (stats.activeScans / Math.max(stats.completedJobs, 1)) * 100)}%`
                          : `${Math.random() * 80 + 20}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Risk Dashboard */}
            <RiskDashboard
              assets={stats.assets || []}
              vulnerabilities={stats.vulnerabilities || []}
              recentScans={scans.slice(0, 5)}
            />

            {/* Quick Actions */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => setShowScanForm(true)}
                  className="flex items-center space-x-3 p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  <Zap className="w-6 h-6 text-blue-400" />
                  <div className="text-left">
                    <p className="font-medium text-gray-200">Quick Network Scan</p>
                    <p className="text-sm text-gray-400">Scan IP addresses and networks</p>
                  </div>
                </button>
                
                <button
                  onClick={() => {
                    setShowScanForm(true);
                    // You could pre-fill web profile here
                  }}
                  className="flex items-center space-x-3 p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  <Globe className="w-6 h-6 text-green-400" />
                  <div className="text-left">
                    <p className="font-medium text-gray-200">Web Security Scan</p>
                    <p className="text-sm text-gray-400">Scan websites and web apps</p>
                  </div>
                </button>
                {/* Enhanced Network Scan */}
                <button
                  onClick={() => setShowEnhancedForm(true)}
                  className="flex items-center space-x-3 p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-left"
                >
                  <Zap className="w-6 h-6 text-purple-400" />
                  <div>
                    <p className="font-medium text-gray-200">Enhanced Network Scan</p>
                    <p className="text-sm text-gray-400">Service enumeration & fingerprinting</p>
                  </div>
                </button>
                
                {/* Enhanced Web Scan */}
                <button
                  onClick={() => {
                    setShowEnhancedForm(true);
                    // You could pre-select web_enhanced here
                  }}
                  className="flex items-center space-x-3 p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-left"
                >
                  <Globe className="w-6 h-6 text-green-400" />
                  <div>
                    <p className="font-medium text-gray-200">Enhanced Web Scan</p>
                    <p className="text-sm text-gray-400">Technology detection & security analysis</p>
                  </div>
                </button>
                
                {/* Quick Scan */}
                <button
                  onClick={() => setShowScanForm(true)}
                  className="flex items-center space-x-3 p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-left"
                >
                  <Server className="w-6 h-6 text-blue-400" />
                  <div>
                    <p className="font-medium text-gray-200">Quick Network Scan</p>
                    <p className="text-sm text-gray-400">Basic port scanning & service detection</p>
                  </div>
                </button>
         
                
                <button
                  onClick={fetchDashboardData}
                  className="flex items-center space-x-3 p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  <RefreshCcw className="w-6 h-6 text-yellow-400" />
                  <div className="text-left">
                    <p className="font-medium text-gray-200">Refresh All Data</p>
                    <p className="text-sm text-gray-400">Update dashboard and statistics</p>
                  </div>
                </button>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-200">Recent Activity</h3>
                <button 
                  onClick={() => setActiveTab('scans')}
                  className="text-blue-400 hover:text-blue-300 text-sm"
                >
                  View All
                </button>
              </div>
              <div className="space-y-3">
                {scans.slice(0, 5).map((scan) => (
                  <div
                    key={scan.id}
                    className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded ${
                        scan.status === 'running' ? 'bg-blue-900/20' :
                        scan.status === 'finished' ? 'bg-green-900/20' :
                        scan.status === 'failed' ? 'bg-red-900/20' :
                        'bg-gray-700'
                      }`}>
                        {scan.status === 'running' && <Activity className="w-4 h-4 text-blue-400" />}
                        {scan.status === 'finished' && <Shield className="w-4 h-4 text-green-400" />}
                        {scan.status === 'failed' && <AlertTriangle className="w-4 h-4 text-red-400" />}
                        {scan.status === 'queued' && <Server className="w-4 h-4 text-gray-400" />}
                      </div>
                      <div>
                        <p className="font-medium text-gray-200">{scan.target}</p>
                        <p className="text-xs text-gray-400">
                          {scan.profile} • {new Date(scan.createdAt).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        scan.status === 'running' ? 'bg-blue-900 text-blue-300' :
                        scan.status === 'finished' ? 'bg-green-900 text-green-300' :
                        scan.status === 'failed' ? 'bg-red-900 text-red-300' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {scan.status}
                      </span>
                      <button
                        onClick={() => fetchScanInsights(scan.id)}
                        className="text-blue-400 hover:text-blue-300"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
                {scans.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No scans yet. Start your first scan to see activity.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Scans Tab */}
        {activeTab === 'scans' && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-200">All Scans</h3>
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-400">
                    {scans.length} total scans
                  </span>
                  <button
                    onClick={() => setShowScanForm(true)}
                    className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
                  >
                    <Play className="w-4 h-4" />
                    <span>New Scan</span>
                  </button>
                </div>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Target
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Progress
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {scans.map((scan) => (
                    <tr key={scan.id} className="hover:bg-gray-700/30 transition-colors">
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-mono text-sm text-gray-200">{scan.target}</p>
                          {scan.asset_id && (
                            <p className="text-xs text-gray-400">Asset: {scan.asset_id.slice(0, 8)}...</p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          scan.profile === 'web' 
                            ? 'bg-purple-900 text-purple-300'
                            : 'bg-blue-900 text-blue-300'
                        }`}>
                          {scan.profile}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          scan.status === 'running' ? 'bg-blue-900 text-blue-300' :
                          scan.status === 'finished' ? 'bg-green-900 text-green-300' :
                          scan.status === 'failed' ? 'bg-red-900 text-red-300' :
                          'bg-gray-700 text-gray-300'
                        }`}>
                          {scan.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-700 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                scan.progress < 100 ? 'bg-blue-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${scan.progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400 w-8">{scan.progress}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-400">
                        {new Date(scan.createdAt).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => fetchScanInsights(scan.id)}
                            className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                          >
                            Insights
                          </button>
                          {scan.status === 'failed' && (
                            <button
                              onClick={() => apiService.retryScan(scan.id).then(fetchDashboardData)}
                              className="text-green-400 hover:text-green-300 text-sm font-medium"
                            >
                              Retry
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {scans.length === 0 && (
                <div className="text-center py-12">
                  <Network className="w-16 h-16 mx-auto mb-4 text-gray-500" />
                  <p className="text-gray-400">No scans found</p>
                  <p className="text-sm text-gray-500 mt-1">Start a new scan to get started</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Insights Tab */}
        {activeTab === 'insights' && (
          <div>
            {selectedScan && scanInsights ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-200">
                      Scan Insights: {selectedScan.target}
                    </h3>
                    <p className="text-sm text-gray-400">
                      Profile: {selectedScan.profile} • 
                      Completed: {selectedScan.finishedAt ? new Date(selectedScan.finishedAt).toLocaleString() : 'N/A'}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedScan(null);
                      setScanInsights(null);
                    }}
                    className="text-gray-400 hover:text-gray-300"
                  >
                    Close
                  </button>
                </div>
                <ScanInsights jobId={selectedScan.id} insights={scanInsights.insights} />
              </div>
            ) : (
              <div className="bg-gray-800 rounded-xl border border-gray-700 p-12 text-center">
                <Eye className="w-16 h-16 mx-auto mb-4 text-gray-500" />
                <h3 className="text-lg font-semibold text-gray-200 mb-2">No Scan Selected</h3>
                <p className="text-gray-400 mb-4">Select a scan from the Recent Scans tab to view detailed insights</p>
                <button
                  onClick={() => setActiveTab('scans')}
                  className="text-blue-400 hover:text-blue-300 font-medium"
                >
                  View All Scans
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;