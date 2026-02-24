import json
import pdfkit
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Template
import os

class ReportGenerator:
    def __init__(self):
        self.template_dir = "app/templates"
    
    def generate_comprehensive_report(self, scan_data: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive security assessment report"""
        
        report_data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "scan_target": scan_data.get('target', 'Unknown'),
                "report_id": f"SEC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                "executive_summary": self._generate_executive_summary(risk_assessment)
            },
            "risk_overview": {
                "total_risk_score": risk_assessment.get('risk_score', 0),
                "risk_level": risk_assessment.get('risk_level', 'UNKNOWN'),
                "findings_count": len(risk_assessment.get('findings', [])),
                "critical_findings": len([f for f in risk_assessment.get('findings', []) 
                                        if f.get('risk_score', 0) >= 40])
            },
            "detailed_findings": self._categorize_findings(risk_assessment.get('findings', [])),
            "network_scan_results": scan_data.get('nmap_results', {}),
            "web_scan_results": scan_data.get('web_results', {}),
            "recommendations": self._generate_recommendations(risk_assessment.get('findings', [])),
            "technical_details": self._extract_technical_details(scan_data)
        }
        
        return report_data
    
    def generate_pdf_report(self, report_data: Dict[str, Any]) -> str:
        """Generate PDF version of the report"""
        try:
            # HTML template for PDF generation
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { border-bottom: 2px solid #333; padding-bottom: 20px; }
                    .risk-score { 
                        background: #f0f0f0; 
                        padding: 20px; 
                        border-radius: 5px;
                        margin: 20px 0;
                    }
                    .critical { color: #d32f2f; font-weight: bold; }
                    .high { color: #f57c00; }
                    .medium { color: #fbc02d; }
                    .low { color: #388e3c; }
                    .finding { margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Security Assessment Report</h1>
                    <p>Target: {{ report_data.metadata.scan_target }}</p>
                    <p>Generated: {{ report_data.metadata.generated_at }}</p>
                </div>
                
                <div class="risk-score">
                    <h2>Risk Overview</h2>
                    <p>Overall Risk Score: <span class="{{ report_data.risk_overview.risk_level|lower }}">
                        {{ report_data.risk_overview.total_risk_score }}/100 ({{ report_data.risk_overview.risk_level }})
                    </span></p>
                    <p>Findings: {{ report_data.risk_overview.findings_count }} total, 
                       {{ report_data.risk_overview.critical_findings }} critical</p>
                </div>
                
                <h2>Executive Summary</h2>
                <p>{{ report_data.metadata.executive_summary }}</p>
                
                <h2>Detailed Findings</h2>
                {% for category, findings in report_data.detailed_findings.items() %}
                    <h3>{{ category|title }} ({{ findings|length }})</h3>
                    {% for finding in findings %}
                        <div class="finding">
                            <strong>{{ finding.title }}</strong> 
                            <span class="{{ finding.risk_level|lower }}">({{ finding.risk_score }})</span>
                            <p>{{ finding.description }}</p>
                            <small>Evidence: {{ finding.evidence }}</small>
                        </div>
                    {% endfor %}
                {% endfor %}
            </body>
            </html>
            """
            
            template = Template(html_template)
            html_content = template.render(report_data=report_data)
            
            # Generate PDF (requires wkhtmltopdf)
            pdf_path = f"/tmp/report_{report_data['metadata']['report_id']}.pdf"
            pdfkit.from_string(html_content, pdf_path)
            
            return pdf_path
        except Exception as e:
            print(f"PDF generation failed: {e}")
            return None
    
    def _generate_executive_summary(self, risk_assessment: Dict[str, Any]) -> str:
        risk_score = risk_assessment.get('risk_score', 0)
        findings = risk_assessment.get('findings', [])
        critical_count = len([f for f in findings if f.get('risk_score', 0) >= 40])
        
        if risk_score >= 80:
            return f"CRITICAL risk environment with {critical_count} critical findings requiring immediate attention."
        elif risk_score >= 60:
            return f"HIGH risk environment with {critical_count} critical findings. Prompt remediation recommended."
        elif risk_score >= 40:
            return f"MEDIUM risk environment with {len(findings)} security findings. Planned remediation advised."
        else:
            return f"LOW risk environment with minimal security concerns. Regular monitoring recommended."
    
    def _categorize_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        categorized = {}
        for finding in findings:
            category = finding.get('category', 'uncategorized')
            if category not in categorized:
                categorized[category] = []
            
            # Add risk level for display
            finding['risk_level'] = self._get_risk_level(finding.get('risk_score', 0))
            categorized[category].append(finding)
        
        return categorized
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        recommendations = set()
        
        for finding in findings:
            category = finding.get('category')
            risk_score = finding.get('risk_score', 0)
            
            if category == 'access_control' and risk_score >= 30:
                recommendations.add("Implement strong access controls and multi-factor authentication")
            elif category == 'network_service' and risk_score >= 25:
                recommendations.add("Harden network services and restrict access to necessary ports only")
            elif category == 'web_security' and risk_score >= 20:
                recommendations.add("Implement web application firewall and security headers")
            elif category == 'software' and risk_score >= 30:
                recommendations.add("Update software to latest patched versions")
            elif risk_score >= 40:
                recommendations.add("Conduct immediate security review and remediation")
        
        return list(recommendations)
    
    def _extract_technical_details(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key technical details for the report"""
        technical = {
            "open_ports": [],
            "services": [],
            "web_technologies": [],
            "network_info": {}
        }
        
        # Extract from nmap results
        if 'nmap_results' in scan_data:
            for host in scan_data['nmap_results'].get('hosts', []):
                technical['open_ports'].extend([
                    f"{port.get('port')}/{port.get('protocol')}" 
                    for port in host.get('ports', []) 
                    if port.get('state') == 'open'
                ])
                
                for port in host.get('ports', []):
                    if port.get('service'):
                        technical['services'].append({
                            'port': port.get('port'),
                            'service': port.get('service'),
                            'version': port.get('version')
                        })
        
        # Extract from web results
        if 'web_results' in scan_data:
            technical['web_technologies'] = scan_data['web_results'].get('technologies', [])
        
        return technical
    
    def _get_risk_level(self, score: int) -> str:
        if score >= 40: return "CRITICAL"
        elif score >= 30: return "HIGH"
        elif score >= 20: return "MEDIUM"
        elif score >= 10: return "LOW"
        else: return "INFO"