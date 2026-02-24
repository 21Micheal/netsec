from .extensions import db
import enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime

# --- Enumerations ---
class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    finished = "finished"
    failed = "failed"

class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VulnStatus(str, enum.Enum):
    OPEN = "open"
    FIXED = "fixed"
    RISK_ACCEPTED = "risk_accepted"
    FALSE_POSITIVE = "false_positive"

class ScanType(str, enum.Enum): # Changed to str enum for consistency/serialization
    network_scan = "network_scan"
    service_enumeration = "service_enumeration"
    vulnerability_assessment = "vulnerability_assessment"
    credential_testing = "credential_testing"
    web_scan = "web_scan"
    ssl_analysis = "ssl_analysis"
    combined = "combined" # Added 'combined' type

# --- Models ---
class Asset(db.Model):
    __tablename__ = "assets"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = db.Column(db.String(45), nullable=False)  # Support IPv6
    hostname = db.Column(db.String(255))
    domain = db.Column(db.String(255))
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    risk_score = db.Column(db.Integer, default=0)
    tags = db.Column(JSONB)  # {"environment": "production", "owner": "team-a"}
    
    # Relationships
    vulnerabilities = db.relationship("Vulnerability", back_populates="asset", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "domain": self.domain,
            "risk_score": self.risk_score,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "tags": self.tags or {},
        }

class ScanJob(db.Model):
    __tablename__ = "scan_jobs"

    __table_args__ = (
        db.Index("idx_scan_jobs_status_created", "status", "created_at"),
        db.Index("idx_scan_jobs_scan_type", "scan_type"), # NEW Index
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target = db.Column(db.Text, nullable=False)
    scan_type = db.Column(db.Enum(ScanType), nullable=False, default=ScanType.network_scan)
    profile = db.Column(db.Text, nullable=False, default="default")
    status = db.Column(db.Enum(JobStatus), nullable=False, default=JobStatus.queued)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    progress = db.Column(db.Integer, default=0)
    log = db.Column(db.Text, default="")
    error = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True) # For consistent error reporting
    insights = db.Column(JSONB, nullable=True) # Kept as insights
    vulnerability_results = db.Column(JSONB, nullable=True) 
    config = db.Column(JSONB, nullable=True) # Scan configuration

    # Foreign key to Asset (optional - not all scans may be associated with a specific asset)
    asset_id = db.Column(UUID(as_uuid=True), db.ForeignKey("assets.id"), nullable=True)
    
    # Relationships
    asset = db.relationship("Asset", backref="scan_jobs")
    results = db.relationship("ScanResult", back_populates="job", cascade="all, delete-orphan") # Kept as results
    web_results = db.relationship("WebScanResult", back_populates="job", cascade="all, delete-orphan")
    vulnerabilities = db.relationship("Vulnerability", back_populates="scan_job", cascade="all, delete-orphan")

    parent_scan_id = db.Column(UUID(as_uuid=True), db.ForeignKey("scan_jobs.id"), nullable=True)
    parent_scan = db.relationship("ScanJob", remote_side=[id], backref="retries")

    @property
    def duration(self):
        if self.finished_at and self.created_at:
            return (self.finished_at - self.created_at).total_seconds()
        return None

    def set_status(self, status, progress=None):
        self.status = status
        # Update updated_at automatically
        self.updated_at = datetime.utcnow()
        if progress is not None:
            self.progress = progress
        if status in [JobStatus.finished, JobStatus.failed]:
            self.finished_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            "id": str(self.id),
            "target": self.target,
            "scan_type": self.scan_type.value if self.scan_type else "network_scan", # NEW FIELD in dict
            "profile": self.profile,
            "status": self.status.value if self.status else "unknown",
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None, # NEW FIELD in dict
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration": self.duration,
            "log": self.log,
            "error": self.error or self.error_message, # Use error_message
            "asset_id": str(self.asset_id) if self.asset_id else None,
            "insights": self.insights, # Kept as insights
            "config": self.config or {}, # NEW FIELD in dict
            "parent_scan_id": str(self.parent_scan_id) if self.parent_scan_id else None,
            "type": "network" if self.profile != "web" else "web" # Kept original 'type' logic for compatibility
        }

    def __repr__(self):
        return f"<ScanJob {self.id} ({self.scan_type.value if self.scan_type else 'unknown'} - {self.status.value})>" # Updated repr

class ScanResult(db.Model):
    __tablename__ = "scan_results"
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    target = db.Column(db.Text, nullable=True)
    port = db.Column(db.Integer, nullable=True)
    protocol = db.Column(db.Text, nullable=True)
    service = db.Column(db.Text, nullable=True)
    version = db.Column(db.Text, nullable=True)
    raw_output = db.Column(JSONB, nullable=True)
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    job = db.relationship("ScanJob", back_populates="results") # Kept back_populates="results"

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": str(self.job_id),
            "target": self.target,
            "port": self.port,
            "protocol": self.protocol,
            "service": self.service,
            "version": self.version,
            "raw_output": self.raw_output,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
        }

class WebScanResult(db.Model):
    __tablename__ = "web_scan_results"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    url = db.Column(db.Text, nullable=False)
    http_status = db.Column(db.Integer, nullable=True)
    headers = db.Column(JSONB, nullable=True)
    cookies = db.Column(JSONB, nullable=True)
    issues = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    job = db.relationship("ScanJob", back_populates="web_results")

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": str(self.job_id),
            "url": self.url,
            "http_status": self.http_status,
            "headers": self.headers,
            "cookies": self.cookies,
            "issues": self.issues,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Vulnerability(db.Model):
    __tablename__ = "vulnerabilities"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = db.Column(UUID(as_uuid=True), db.ForeignKey("assets.id"), nullable=False)
    scan_job_id = db.Column(UUID(as_uuid=True), db.ForeignKey("scan_jobs.id"), nullable=False)
    cve_id = db.Column(db.String(50))
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    severity = db.Column(db.String(20))  # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score = db.Column(db.Float)
    port = db.Column(db.Integer)
    protocol = db.Column(db.String(10))
    proof = db.Column(JSONB)  # Evidence of vulnerability
    status = db.Column(db.Enum(VulnStatus), default=VulnStatus.OPEN)
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow)
    fixed_at = db.Column(db.DateTime)

    # Relationships
    asset = db.relationship("Asset", back_populates="vulnerabilities")
    scan_job = db.relationship("ScanJob", back_populates="vulnerabilities")

    def to_dict(self):
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "scan_job_id": str(self.scan_job_id),
            "cve_id": self.cve_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "port": self.port,
            "protocol": self.protocol,
            "proof": self.proof,
            "status": self.status.value if self.status else "open",
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "fixed_at": self.fixed_at.isoformat() if self.fixed_at else None
        }

class IntelligenceReport(db.Model):
    __tablename__ = "intelligence_reports"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target = db.Column(db.String(500), nullable=False)
    report_type = db.Column(db.String(50))  # network, web, comprehensive
    data = db.Column(JSONB)  # Complete scan results
    risk_assessment = db.Column(JSONB)  # Risk analysis
    recommendations = db.Column(JSONB)  # Remediation steps
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "target": self.target,
            "report_type": self.report_type,
            "risk_score": self.data.get('risk_assessment', {}).get('risk_score', 0) if self.data else 0,
            "generated_at": self.generated_at.isoformat(),
            "findings_count": len(self.data.get('vulnerabilities', [])) if self.data else 0
        }