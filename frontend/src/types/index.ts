// Core Scan Job Types
export interface ScanJob {
  id: string;
  target: string;
  profile: string;
  status: 'queued' | 'running' | 'finished' | 'failed';
  progress: number;
  createdAt: string;
  finishedAt?: string;
  duration?: number;
  log?: string;
  error?: string;
  asset_id?: string;
  insights?: ScanInsights;
  type: string;
  parent_scan_id?: string;
}

export interface ScanResult {
  id: number;
  job_id: string;
  target: string;
  port?: number;
  protocol?: string;
  service?: string;
  version?: string;
  raw_output?: any;
  discovered_at: string;
}

export interface WebScanResult {
  id: number;
  job_id: string;
  url: string;
  http_status?: number;
  headers?: Record<string, string>;
  cookies?: Record<string, string>;
  issues?: SecurityIssue[];
  created_at: string;
}

// Security Finding Types
export interface SecurityIssue {
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  message: string;
  recommendation?: string;
  evidence?: string;
  port?: number;
  service?: string;
  category?: string;
}

export interface SecurityIndicator {
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  message: string;
  port?: number;
  service?: string;
  protocol?: string;
  evidence?: string;
  recommendation?: string;
}

// Asset Management Types
export interface Asset {
  id: string;
  ip_address: string;
  hostname?: string;
  domain?: string;
  risk_score: number;
  first_seen: string;
  last_seen: string;
  tags?: Record<string, any>;
  vulnerability_count?: number;
  critical_vulnerabilities?: number;
  last_scan?: string;
}

export interface Vulnerability {
  id: string;
  asset_id: string;
  scan_job_id: string;
  cve_id?: string;
  title: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  cvss_score?: number;
  port?: number;
  protocol?: string;
  proof?: any;
  status: 'open' | 'fixed' | 'risk_accepted' | 'false_positive';
  discovered_at: string;
  fixed_at?: string;
}

// Scan Insights Types
export interface ScanInsights {
  target: string;
  open_ports?: PortInfo[];
  services?: ServiceInfo[];
  operating_system?: string;
  service_versions?: Record<string, number>;
  security_indicators?: SecurityIndicator[];
  web_results?: WebScanData;
  summary: ScanSummary;
}

export interface PortInfo {
  port: number;
  protocol: string;
  service: string;
  version?: string;
  product?: string;
  state: string;
}

export interface ServiceInfo {
  port: number;
  name: string;
  version?: string;
  product?: string;
}

export interface WebScanData {
  url: string;
  base_domain: string;
  final_url?: string;
  accessible: boolean;
  error?: string;
  status_code?: number;
  headers: Record<string, string>;
  cookies: Record<string, string>;
  security_headers: SecurityHeaders;
  ssl_info?: SSLInfo;
  response_time?: number;
  content_length?: number;
  used_protocol?: string;
  technologies?: string[];
  redirects?: string[];
  scan_time: string;
}

export interface SecurityHeaders {
  [key: string]: string | string[] | number | undefined;
  missing_headers?: string[];
  score?: number;
}

export interface SSLInfo {
  subject?: Record<string, string>;
  issuer?: Record<string, string>;
  valid_from?: string;
  valid_until?: string;
  version?: string;
  san?: string[];
  error?: string;
}

export interface ScanSummary {
  total_open_ports: number;
  unique_services: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO' | 'UNKNOWN';
  http_status?: number;
  headers_count?: number;
  cookies_count?: number;
  security_issues?: number;
  common_services?: string[];
}

// Dashboard Statistics Types
export interface DashboardStats {
  activeScans: number;
  completedJobs: number;
  systemLoad: number;
  alerts: number;
  totalScans?: number;
  queuedScans?: number;
  successRate?: number;
  totalAssets?: number;
  totalVulnerabilities?: number;
  criticalVulnerabilities?: number;
  avgRiskScore?: number;
  assets?: Asset[];
  vulnerabilities?: Vulnerability[];
  recentFindings?: RecentFinding[];
  serviceDistribution?: Record<string, number>;
  riskDistribution?: RiskDistribution;
}

export interface RecentFinding {
  id: string;
  title: string;
  severity: string;
  asset: string;
  discovered_at: string;
}

export interface RiskDistribution {
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
  INFO: number;
}

// Real-time Communication Types
export type SocketEventType = 
  | 'scan_update' 
  | 'job_update' 
  | 'scan_log' 
  | 'traffic_update' 
  | 'error'
  | 'connected'
  | 'subscribed'
  | 'unsubscribed'
  | 'pong'
  | 'scan_completed'
  | 'scan_failed';

export interface SocketEvent {
  type: SocketEventType;
  data: any;
}

export interface ScanUpdateData {
  job_id: string;
  status: 'queued' | 'running' | 'finished' | 'failed';
  progress: number;
  target: string;
  profile: string;
  _source?: string;
  _timestamp?: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface ScanCreationResponse {
  job_id: string;
  message: string;
  auto_detected_profile?: string;
}

export interface InsightsResponse {
  job_id: string;
  target: string;
  profile: string;
  status: string;
  insights: ScanInsights;
  vulnerabilities: Vulnerability[];
  summary: {
    open_ports: number;
    services_found: number;
    security_indicators: number;
    risk_level: string;
  };
}

// Form and UI Types
export interface ScanFormData {
  target: string;
  profile: 'default' | 'quick' | 'detailed' | 'comprehensive' | 'web';
  scan_type?: 'network' | 'web' | 'combined';
}

export interface QuickScanExample {
  target: string;
  profile: string;
  description: string;
}

// Chart and Visualization Types
export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
    borderColor: string[];
    borderWidth: number;
  }[];
}

export interface ServiceDistribution {
  [service: string]: number;
}

export interface RiskMetrics {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

// Report and Export Types
export interface IntelligenceReport {
  id: string;
  target: string;
  report_type: string;
  data: any;
  risk_assessment: any;
  recommendations: string[];
  generated_at: string;
  risk_score?: number;
  findings_count?: number;
}

export interface ReportData {
  metadata: {
    generated_at: string;
    scan_target: string;
    report_id: string;
    executive_summary: string;
  };
  risk_overview: {
    total_risk_score: number;
    risk_level: string;
    findings_count: number;
    critical_findings: number;
  };
  detailed_findings: Record<string, SecurityIssue[]>;
  network_scan_results: any;
  web_scan_results: any;
  recommendations: string[];
  technical_details: {
    open_ports: string[];
    services: ServiceInfo[];
    web_technologies: string[];
    network_info: Record<string, any>;
  };
}

// Filter and Search Types
export interface ScanFilter {
  status?: string[];
  profile?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  target?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// Settings and Configuration Types
export interface AppSettings {
  scanSettings: {
    defaultProfile: string;
    timeout: number;
    maxConcurrentScans: number;
    autoDetectWebTargets: boolean;
  };
  notificationSettings: {
    emailNotifications: boolean;
    webhookUrl?: string;
    alertThreshold: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  };
  securitySettings: {
    allowedTargets: string[];
    blockedTargets: string[];
    rateLimiting: boolean;
  };
}

// Enum-like Constants
export const ScanStatus = {
  QUEUED: 'queued',
  RUNNING: 'running',
  FINISHED: 'finished',
  FAILED: 'failed'
} as const;

export const ScanProfile = {
  DEFAULT: 'default',
  QUICK: 'quick',
  DETAILED: 'detailed',
  COMPREHENSIVE: 'comprehensive',
  WEB: 'web'
} as const;

export const SeverityLevel = {
  CRITICAL: 'CRITICAL',
  HIGH: 'HIGH',
  MEDIUM: 'MEDIUM',
  LOW: 'LOW',
  INFO: 'INFO'
} as const;

// Utility Types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type Require<T, K extends keyof T> = T & Required<Pick<T, K>>;

// API Error Types
export interface ApiError {
  code: number;
  message: string;
  details?: any;
  timestamp: string;
}

// WebSocket Connection Types
export interface WebSocketState {
  isConnected: boolean;
  lastMessage: SocketEvent | null;
  subscribedJobs: Set<string>;
  connectionId?: string;
}

// Real-time Metrics Types
export interface LiveMetrics {
  activeScans: number;
  systemLoad: number;
  networkTraffic: number;
  memoryUsage: number;
  timestamp: string;
}

// Export all types
export type {
  // Re-export for convenience
  ScanJob as IScanJob,
  ScanResult as IScanResult,
  WebScanResult as IWebScanResult,
  SecurityIssue as ISecurityIssue,
  Asset as IAsset,
  Vulnerability as IVulnerability,
  ScanInsights as IScanInsights,
  DashboardStats as IDashboardStats
};