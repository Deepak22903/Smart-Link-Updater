"""
HTML Structure Monitoring System

Detects when source websites change their HTML structure,
which would break extractors. Provides alerts and health checks.

Now uses MongoDB for persistent storage instead of JSON files.
"""

import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from .models import (
    HTMLFingerprint,
    ExtractionHistory,
    SourceMonitoring,
    Alert
)
from . import mongo_storage


class HTMLMonitor:
    """Monitor HTML structure changes and extraction health"""
    
    def __init__(self):
        """Initialize HTML monitor with MongoDB storage"""
        pass
    
    def _load_monitoring(self) -> Dict[str, SourceMonitoring]:
        """Load monitoring data for all sources from MongoDB"""
        try:
            data = mongo_storage.get_all_source_monitoring()
            return {
                url: SourceMonitoring(**info)
                for url, info in data.items()
            }
        except Exception as e:
            print(f"Error loading monitoring data: {e}")
            return {}
    
    def _save_monitoring(self, monitoring: Dict[str, SourceMonitoring]):
        """Save monitoring data to MongoDB"""
        for url, info in monitoring.items():
            mongo_storage.save_source_monitoring(info.model_dump())
    
    def _load_alerts(self) -> List[Alert]:
        """Load alert history from MongoDB"""
        try:
            data = mongo_storage.get_alerts(limit=100)
            return [Alert(**alert) for alert in data]
        except Exception:
            return []
    
    def _save_alerts(self, alerts: List[Alert]):
        """Save alerts to MongoDB (not needed, alerts are saved individually now)"""
        # This method is kept for compatibility but alerts are now saved individually
        pass
    
    def compute_fingerprint(self, html: str) -> HTMLFingerprint:
        """
        Compute HTML structure fingerprint.
        
        Tracks:
        - DOM structure hash (headings, containers)
        - Heading hierarchy and text
        - Critical CSS selectors
        - Page size
        - Element counts
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract heading structure
        headings = []
        for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(strip=True)[:50]  # First 50 chars
                if text:
                    headings.append(f"{tag_name}:{text}")
        
        # Also check <strong> tags that might be date headers
        for strong in soup.find_all('strong'):
            text = strong.get_text(strip=True)
            if text and len(text) < 50 and any(char.isdigit() for char in text):
                headings.append(f"strong:{text}")
        
        # Identify critical selectors (common patterns for reward sites)
        critical_selectors = []
        if soup.select('.reward-link'):
            critical_selectors.append('.reward-link')
        if soup.select('div[data-link]'):
            critical_selectors.append('div[data-link]')
        if soup.select('a.button'):
            critical_selectors.append('a.button')
        if soup.select('.links-container'):
            critical_selectors.append('.links-container')
        
        # Compute DOM hash (structure, not content)
        # We hash: tag names, classes, and hierarchy
        dom_structure = []
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'section', 'article', 'div']):
            if element.get('class'):
                dom_structure.append(f"{element.name}.{'.'.join(element.get('class'))}")
            else:
                dom_structure.append(element.name)
        
        dom_hash = hashlib.md5(
            '|'.join(dom_structure).encode('utf-8')
        ).hexdigest()[:16]
        
        # Count elements
        all_links = soup.find_all('a', href=True)
        link_count = len([a for a in all_links if a.get('href', '').startswith('http')])
        
        return HTMLFingerprint(
            dom_hash=dom_hash,
            heading_structure=headings[:30],  # First 30 headings
            critical_selectors=critical_selectors,
            html_size=len(html),
            last_updated=datetime.utcnow().isoformat(),
            heading_count=len(headings),
            link_count=link_count
        )
    
    def check_structure_change(
        self,
        source_url: str,
        html: str,
        threshold: float = 0.3
    ) -> Tuple[bool, List[str]]:
        """
        Check if HTML structure has changed significantly.
        
        Returns: (has_changed, reasons)
        """
        monitoring = self._load_monitoring()
        
        # If no previous fingerprint, this is first check
        if source_url not in monitoring or not monitoring[source_url].fingerprint:
            return False, ["First check - no baseline"]
        
        old_fp = monitoring[source_url].fingerprint
        new_fp = self.compute_fingerprint(html)
        
        changes = []
        has_changed = False
        
        # 1. Check DOM hash
        if old_fp.dom_hash != new_fp.dom_hash:
            changes.append(f"DOM structure changed (hash: {old_fp.dom_hash} → {new_fp.dom_hash})")
            has_changed = True
        
        # 2. Check heading count (allow 20% variance)
        heading_diff = abs(old_fp.heading_count - new_fp.heading_count) / max(old_fp.heading_count, 1)
        if heading_diff > 0.2:
            changes.append(
                f"Heading count changed significantly: {old_fp.heading_count} → {new_fp.heading_count}"
            )
            has_changed = True
        
        # 3. Check HTML size (allow 40% variance)
        size_diff = abs(old_fp.html_size - new_fp.html_size) / max(old_fp.html_size, 1)
        if size_diff > 0.4:
            changes.append(
                f"Page size changed {size_diff*100:.1f}%: {old_fp.html_size} → {new_fp.html_size} bytes"
            )
            has_changed = True
        
        # 4. Check if critical selectors still exist
        missing_selectors = [
            sel for sel in old_fp.critical_selectors
            if sel not in new_fp.critical_selectors
        ]
        if missing_selectors:
            changes.append(f"Missing selectors: {', '.join(missing_selectors)}")
            has_changed = True
        
        # 5. Check link count (allow 30% variance)
        if old_fp.link_count > 0:
            link_diff = abs(old_fp.link_count - new_fp.link_count) / old_fp.link_count
            if link_diff > 0.3:
                changes.append(
                    f"Link count changed {link_diff*100:.1f}%: {old_fp.link_count} → {new_fp.link_count}"
                )
                # Don't set has_changed=True here, as this might be normal daily variation
        
        return has_changed, changes
    
    def record_extraction(
        self,
        source_url: str,
        date: str,
        links_found: int,
        confidence: float,
        success: bool = True,
        error: Optional[str] = None,
        html: Optional[str] = None
    ):
        """
        Record extraction attempt and update monitoring.
        
        Also updates HTML fingerprint if html is provided.
        """
        monitoring = self._load_monitoring()
        
        # Initialize if new source
        if source_url not in monitoring:
            monitoring[source_url] = SourceMonitoring(
                source_url=source_url,
                last_check=datetime.utcnow().isoformat(),
                extraction_history=[]
            )
        
        source_mon = monitoring[source_url]
        
        # Add extraction history
        history = ExtractionHistory(
            date=date,
            links_found=links_found,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat(),
            success=success,
            error=error
        )
        source_mon.extraction_history.append(history)
        
        # Keep only last 30 days
        source_mon.extraction_history = source_mon.extraction_history[-30:]
        
        # Update fingerprint if HTML provided
        if html:
            new_fp = self.compute_fingerprint(html)
            
            # Check for structure changes
            if source_mon.fingerprint:
                has_changed, reasons = self.check_structure_change(source_url, html)
                if has_changed:
                    self._create_alert(
                        alert_type="structure_changed",
                        source_url=source_url,
                        severity="warning",
                        message=f"HTML structure changed for {source_url}",
                        details={"reasons": reasons}
                    )
            
            source_mon.fingerprint = new_fp
        
        # Update status based on extraction results
        source_mon.last_check = datetime.utcnow().isoformat()
        
        if not success:
            source_mon.consecutive_failures += 1
        else:
            source_mon.consecutive_failures = 0
        
        # Determine status
        if source_mon.consecutive_failures >= 3:
            source_mon.status = "failing"
        elif source_mon.consecutive_failures > 0:
            source_mon.status = "warning"
        else:
            source_mon.status = "healthy"
        
        monitoring[source_url] = source_mon
        self._save_monitoring(monitoring)
        
        # Check for alert conditions
        self._check_alert_conditions(source_url, source_mon)
    
    def _check_alert_conditions(self, source_url: str, source_mon: SourceMonitoring):
        """Check if any alert conditions are met"""
        
        # Get today's extractions
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_extractions = [
            h for h in source_mon.extraction_history
            if h.date == today
        ]
        
        # Alert: Zero links found today (after 12 PM)
        if today_extractions:
            total_links_today = sum(h.links_found for h in today_extractions)
            if total_links_today == 0:
                current_hour = datetime.utcnow().hour
                if current_hour >= 12:  # Only alert after noon
                    self._create_alert(
                        alert_type="zero_links",
                        source_url=source_url,
                        severity="critical",
                        message=f"Zero links extracted today from {source_url}",
                        details={
                            "date": today,
                            "attempts": len(today_extractions)
                        }
                    )
        
        # Alert: Low confidence
        if today_extractions:
            avg_confidence = sum(h.confidence for h in today_extractions) / len(today_extractions)
            
            # Compare to historical average
            if len(source_mon.extraction_history) > 5:
                historical = [h for h in source_mon.extraction_history if h.date != today]
                if historical:
                    hist_avg = sum(h.confidence for h in historical) / len(historical)
                    
                    # Alert if confidence dropped significantly
                    if hist_avg > 0.7 and avg_confidence < 0.5:
                        self._create_alert(
                            alert_type="low_confidence",
                            source_url=source_url,
                            severity="warning",
                            message=f"Confidence dropped significantly for {source_url}",
                            details={
                                "historical_avg": hist_avg,
                                "today_avg": avg_confidence,
                                "date": today
                            }
                        )
        
        # Alert: Consecutive failures
        if source_mon.consecutive_failures >= 3:
            self._create_alert(
                alert_type="consecutive_failures",
                source_url=source_url,
                severity="critical",
                message=f"3+ consecutive failures for {source_url}",
                details={
                    "consecutive_failures": source_mon.consecutive_failures
                }
            )
        
        # Alert: Significant decrease in links (50% drop)
        if len(source_mon.extraction_history) > 7:
            recent = source_mon.extraction_history[-7:]
            today_avg = sum(h.links_found for h in recent if h.date == today) / max(len([h for h in recent if h.date == today]), 1)
            
            older = source_mon.extraction_history[-14:-7]
            if older:
                old_avg = sum(h.links_found for h in older) / len(older)
                
                if old_avg > 5 and today_avg < old_avg * 0.5:
                    self._create_alert(
                        alert_type="link_count_drop",
                        source_url=source_url,
                        severity="warning",
                        message=f"Link count dropped significantly for {source_url}",
                        details={
                            "old_average": old_avg,
                            "today_average": today_avg,
                            "drop_percentage": (1 - today_avg/old_avg) * 100
                        }
                    )
    
    def _create_alert(
        self,
        alert_type: str,
        source_url: str,
        severity: str,
        message: str,
        details: Optional[Dict] = None
    ):
        """Create and save alert to MongoDB"""
        alerts = self._load_alerts()
        
        # Check if similar alert was created recently (avoid spam)
        recent_cutoff = datetime.utcnow() - timedelta(hours=6)
        recent_alerts = [
            a for a in alerts
            if a.source_url == source_url
            and a.alert_type == alert_type
            and datetime.fromisoformat(a.timestamp) > recent_cutoff
        ]
        
        if recent_alerts:
            return  # Don't create duplicate alert
        
        alert_data = {
            "alert_type": alert_type,
            "source_url": source_url,
            "severity": severity,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "notified": False,
            "details": details or {}
        }
        
        # Save directly to MongoDB
        mongo_storage.save_alert(alert_data)
    
    def get_source_health(self, source_url: str) -> Dict:
        """Get health status for a source"""
        monitoring = self._load_monitoring()
        
        if source_url not in monitoring:
            return {
                "status": "unknown",
                "message": "No monitoring data available"
            }
        
        source_mon = monitoring[source_url]
        
        # Get recent stats
        recent = source_mon.extraction_history[-7:] if source_mon.extraction_history else []
        
        avg_links = sum(h.links_found for h in recent) / len(recent) if recent else 0
        avg_confidence = sum(h.confidence for h in recent) / len(recent) if recent else 0
        success_rate = sum(1 for h in recent if h.success) / len(recent) if recent else 0
        
        return {
            "status": source_mon.status,
            "consecutive_failures": source_mon.consecutive_failures,
            "last_check": source_mon.last_check,
            "recent_stats": {
                "avg_links": round(avg_links, 1),
                "avg_confidence": round(avg_confidence, 2),
                "success_rate": round(success_rate * 100, 1)
            },
            "fingerprint": source_mon.fingerprint.model_dump() if source_mon.fingerprint else None
        }
    
    def get_all_health(self) -> Dict[str, Dict]:
        """Get health status for all monitored sources"""
        monitoring = self._load_monitoring()
        return {
            url: self.get_source_health(url)
            for url in monitoring.keys()
        }
    
    def get_unnotified_alerts(self) -> List[Alert]:
        """Get alerts that haven't been sent yet from MongoDB"""
        alerts_data = mongo_storage.get_unnotified_alerts()
        return [Alert(**alert) for alert in alerts_data]
    
    def mark_alerts_notified(self, alert_ids: List[str]):
        """Mark alerts as notified in MongoDB"""
        mongo_storage.mark_alerts_notified(alert_ids)
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from last N hours from MongoDB"""
        all_alerts = mongo_storage.get_alerts(limit=1000)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            Alert(**a) for a in all_alerts
            if datetime.fromisoformat(a["timestamp"]) > cutoff
        ]


# Global instance
_monitor = None

def get_monitor() -> HTMLMonitor:
    """Get global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = HTMLMonitor()
    return _monitor
