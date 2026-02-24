-- Create UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types first
CREATE TYPE jobstatus AS ENUM ('queued', 'running', 'finished', 'failed');
CREATE TYPE scanstatus AS ENUM ('pending', 'running', 'finished', 'failed', 'cancelled');
CREATE TYPE vulnstatus AS ENUM ('open', 'fixed', 'risk_accepted', 'false_positive');
CREATE TYPE scantype AS ENUM ('network_scan', 'service_enumeration', 'vulnerability_assessment', 'credential_testing', 'web_scan', 'ssl_analysis', 'combined');

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user'
);

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip_address VARCHAR(45) NOT NULL,
    hostname VARCHAR(255),
    domain VARCHAR(255),
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    risk_score INTEGER DEFAULT 0,
    tags JSONB
);

-- Scan jobs table with all required columns
CREATE TABLE IF NOT EXISTS scan_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target TEXT NOT NULL,
    scan_type scantype NOT NULL DEFAULT 'network_scan',
    profile TEXT NOT NULL DEFAULT 'default',
    status jobstatus NOT NULL DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    progress INTEGER DEFAULT 0,
    log TEXT DEFAULT '',
    error TEXT,
    error_message TEXT,
    insights JSONB,
    vulnerability_results JSONB,
    config JSONB,
    asset_id UUID REFERENCES assets(id),
    parent_scan_id UUID REFERENCES scan_jobs(id)
);

-- Create indexes for scan_jobs
CREATE INDEX IF NOT EXISTS idx_scan_jobs_status_created ON scan_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_scan_type ON scan_jobs(scan_type);

-- Scan results table
CREATE TABLE IF NOT EXISTS scan_results (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES scan_jobs(id) ON DELETE CASCADE,
    target TEXT,
    port INTEGER,
    protocol TEXT,
    service TEXT,
    version TEXT,
    raw_output JSONB,
    discovered_at TIMESTAMP DEFAULT NOW()
);

-- Web scan results table
CREATE TABLE IF NOT EXISTS web_scan_results (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES scan_jobs(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    http_status INTEGER,
    headers JSONB,
    cookies JSONB,
    issues JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vulnerabilities table
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(id) NOT NULL,
    scan_job_id UUID REFERENCES scan_jobs(id) NOT NULL,
    cve_id VARCHAR(50),
    title VARCHAR(500),
    description TEXT,
    severity VARCHAR(20),
    cvss_score FLOAT,
    port INTEGER,
    protocol VARCHAR(10),
    proof JSONB,
    status vulnstatus DEFAULT 'open',
    discovered_at TIMESTAMP DEFAULT NOW(),
    fixed_at TIMESTAMP
);

-- Intelligence reports table
CREATE TABLE IF NOT EXISTS intelligence_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target VARCHAR(500) NOT NULL,
    report_type VARCHAR(50),
    data JSONB,
    risk_assessment JSONB,
    recommendations JSONB,
    generated_at TIMESTAMP DEFAULT NOW()
);