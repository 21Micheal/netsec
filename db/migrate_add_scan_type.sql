-- Migration: Add scan_type and other missing columns to scan_jobs table
-- Run this script if you have an existing database missing the scan_type column

-- First, create the ENUM type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scantype') THEN
        CREATE TYPE scantype AS ENUM ('network_scan', 'service_enumeration', 'vulnerability_assessment', 'credential_testing', 'web_scan', 'ssl_analysis', 'combined');
    END IF;
END
$$;

-- Create jobstatus enum if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'jobstatus') THEN
        CREATE TYPE jobstatus AS ENUM ('queued', 'running', 'finished', 'failed');
    END IF;
END
$$;

-- Add scan_type column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'scan_type') THEN
        ALTER TABLE scan_jobs ADD COLUMN scan_type scantype NOT NULL DEFAULT 'network_scan';
    END IF;
END
$$;

-- Add updated_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'updated_at') THEN
        ALTER TABLE scan_jobs ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    END IF;
END
$$;

-- Add progress column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'progress') THEN
        ALTER TABLE scan_jobs ADD COLUMN progress INTEGER DEFAULT 0;
    END IF;
END
$$;

-- Add log column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'log') THEN
        ALTER TABLE scan_jobs ADD COLUMN log TEXT DEFAULT '';
    END IF;
END
$$;

-- Add error column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'error') THEN
        ALTER TABLE scan_jobs ADD COLUMN error TEXT;
    END IF;
END
$$;

-- Add error_message column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'error_message') THEN
        ALTER TABLE scan_jobs ADD COLUMN error_message TEXT;
    END IF;
END
$$;

-- Add insights column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'insights') THEN
        ALTER TABLE scan_jobs ADD COLUMN insights JSONB;
    END IF;
END
$$;

-- Add vulnerability_results column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'vulnerability_results') THEN
        ALTER TABLE scan_jobs ADD COLUMN vulnerability_results JSONB;
    END IF;
END
$$;

-- Add config column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'config') THEN
        ALTER TABLE scan_jobs ADD COLUMN config JSONB;
    END IF;
END
$$;

-- Add asset_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'asset_id') THEN
        ALTER TABLE scan_jobs ADD COLUMN asset_id UUID;
    END IF;
END
$$;

-- Add parent_scan_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'scan_jobs' AND column_name = 'parent_scan_id') THEN
        ALTER TABLE scan_jobs ADD COLUMN parent_scan_id UUID REFERENCES scan_jobs(id);
    END IF;
END
$$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_scan_jobs_status_created ON scan_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_scan_type ON scan_jobs(scan_type);

-- Update the status column to use enum type if it's currently text
-- First check if status is text type and convert if needed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'scan_jobs' 
        AND column_name = 'status' 
        AND data_type = 'text'
    ) THEN
        -- Create a temporary column with the enum type
        ALTER TABLE scan_jobs ADD COLUMN status_new jobstatus DEFAULT 'queued';
        
        -- Copy data converting text to enum
        UPDATE scan_jobs SET status_new = status::jobstatus WHERE status IN ('queued', 'running', 'finished', 'failed');
        
        -- Drop old column and rename new one
        ALTER TABLE scan_jobs DROP COLUMN status;
        ALTER TABLE scan_jobs RENAME COLUMN status_new TO status;
    END IF;
END
$$;