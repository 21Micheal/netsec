from app.models import Asset, ScanJob, Vulnerability
from app.extensions import db
from datetime import datetime
import ipaddress

class AssetManager:
    def discover_asset_from_scan(self, scan_job: ScanJob, scan_results: dict):
        """Discover and update assets from scan results"""
        try:
            target = scan_job.target
            
            # Check if target is an IP address
            try:
                ipaddress.ip_address(target)
                ip_address = target
                hostname = None
            except ValueError:
                # Target is a hostname/domain
                ip_address = None
                hostname = target
            
            # Look for existing asset
            if ip_address:
                asset = Asset.query.filter_by(ip_address=ip_address).first()
            else:
                asset = Asset.query.filter_by(hostname=hostname).first()
            
            if not asset:
                # Create new asset
                asset = Asset(
                    ip_address=ip_address or '',
                    hostname=hostname,
                    domain=self._extract_domain(hostname) if hostname else None
                )
                db.session.add(asset)
            
            # Update asset information from scan
            asset.last_seen = datetime.utcnow()
            
            # Associate scan job with asset
            scan_job.asset_id = asset.id
            
            db.session.commit()
            return asset
            
        except Exception as e:
            print(f"Asset discovery failed: {e}")
            return None
    
    def update_asset_risk_score(self, asset_id: str):
        """Update asset risk score based on vulnerabilities"""
        try:
            asset = Asset.query.get(asset_id)
            if not asset:
                return
            
            # Calculate risk score from vulnerabilities
            vulnerabilities = Vulnerability.query.filter_by(asset_id=asset_id).all()
            
            risk_weights = {
                'CRITICAL': 40,
                'HIGH': 30,
                'MEDIUM': 20,
                'LOW': 10
            }
            
            total_risk = 0
            for vuln in vulnerabilities:
                if vuln.status.value != 'fixed':
                    total_risk += risk_weights.get(vuln.severity, 10)
            
            asset.risk_score = min(total_risk, 100)
            db.session.commit()
            
        except Exception as e:
            print(f"Risk score update failed: {e}")
    
    def _extract_domain(self, hostname: str) -> str:
        """Extract domain from hostname"""
        parts = hostname.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return hostname
    
    def get_assets_with_risk(self) -> list:
        """Get all assets with their risk information"""
        assets = Asset.query.all()
        
        result = []
        for asset in assets:
            vuln_count = Vulnerability.query.filter_by(asset_id=asset.id).count()
            critical_vulns = Vulnerability.query.filter_by(
                asset_id=asset.id, 
                severity='CRITICAL'
            ).count()
            
            result.append({
                **asset.to_dict(),
                "vulnerability_count": vuln_count,
                "critical_vulnerabilities": critical_vulns,
                "last_scan": self._get_last_scan_date(asset.id)
            })
        
        return result
    
    def _get_last_scan_date(self, asset_id: str) -> str:
        """Get the last scan date for an asset"""
        last_scan = ScanJob.query.filter_by(asset_id=asset_id)\
            .order_by(ScanJob.created_at.desc())\
            .first()
        
        return last_scan.created_at.isoformat() if last_scan else None