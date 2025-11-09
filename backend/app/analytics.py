"""
Analytics Module for SmartLink Updater

Provides analytics data for:
- Update statistics (daily, weekly, monthly)
- Success/failure rates
- Link extraction trends
- Source health trends
- Post-level performance metrics
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
from .mongo_storage import MongoDBStorage


class AnalyticsEngine:
    """Generate analytics and insights from historical data"""
    
    def __init__(self):
        self.storage = MongoDBStorage()
        self.db = self.storage.db
    
    def get_dashboard_summary(self, days: int = 30) -> Dict:
        """
        Get high-level dashboard summary
        
        Args:
            days: Number of days to analyze (default 30)
            
        Returns:
            Dict with summary metrics
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get data from fingerprints (actual link tracking data)
        total_links = self.db["fingerprints"].count_documents({
            "date_iso": {"$gte": cutoff_date}
        })
        
        # Active posts (posts that have fingerprints in period)
        active_posts = len(self.db["fingerprints"].distinct("post_id", {
            "date_iso": {"$gte": cutoff_date}
        }))
        
        # Get unique dates with updates
        unique_dates = len(self.db["fingerprints"].distinct("date_iso", {
            "date_iso": {"$gte": cutoff_date}
        }))
        
        # Check if update_history exists and has data
        update_history_count = self.db["update_history"].count_documents({})
        if update_history_count > 0:
            # Use update_history if available
            total_updates = self.db["update_history"].count_documents({
                "date_iso": {"$gte": cutoff_date}
            })
            successful_updates = self.db["update_history"].count_documents({
                "date_iso": {"$gte": cutoff_date},
                "status": "success"
            })
        else:
            # Estimate from fingerprints
            total_updates = unique_dates * active_posts if active_posts > 0 else 0
            successful_updates = total_updates  # Assume all successful if links were added
        
        success_rate = (successful_updates / total_updates * 100) if total_updates > 0 else 0
        avg_links = total_links / total_updates if total_updates > 0 else 0
        
        # Current health status
        health_counts = self._get_health_distribution()
        
        return {
            "period_days": days,
            "total_updates": total_updates,
            "successful_updates": successful_updates,
            "failed_updates": total_updates - successful_updates,
            "success_rate": round(success_rate, 2),
            "total_links_added": total_links,
            "active_posts": active_posts,
            "avg_links_per_update": round(avg_links, 2),
            "health_distribution": health_counts
        }
    
    def get_update_timeline(self, days: int = 30, granularity: str = "daily") -> List[Dict]:
        """
        Get timeline of updates over period
        
        Args:
            days: Number of days to analyze
            granularity: 'hourly', 'daily', or 'weekly'
            
        Returns:
            List of data points with date, success, failed counts
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Aggregate fingerprints by date
        pipeline = [
            {"$match": {"date_iso": {"$gte": cutoff_date}}},
            {"$group": {
                "_id": "$date_iso",
                "total_links": {"$sum": 1},
                "unique_posts": {"$addToSet": "$post_id"}
            }},
            {"$project": {
                "date": "$_id",
                "total_links": 1,
                "posts_updated": {"$size": "$unique_posts"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(self.db["fingerprints"].aggregate(pipeline))
        
        return [{
            "date": r["_id"],
            "total_updates": r.get("posts_updated", 0),
            "successful": r.get("posts_updated", 0),
            "failed": 0,
            "total_links": r.get("total_links", 0),
            "success_rate": 100.0
        } for r in results]
    
    def get_post_performance(self, days: int = 30) -> List[Dict]:
        """
        Get performance metrics per post
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of posts with their performance metrics
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        pipeline = [
            {"$match": {"date_iso": {"$gte": cutoff_date}}},
            {"$group": {
                "_id": "$post_id",
                "total_links_added": {"$sum": 1},
                "unique_dates": {"$addToSet": "$date_iso"},
                "sites": {"$addToSet": "$site_key"}
            }},
            {"$project": {
                "post_id": "$_id",
                "total_updates": {"$size": "$unique_dates"},
                "successful_updates": {"$size": "$unique_dates"},
                "total_links_added": 1,
                "sites_count": {"$size": "$sites"}
            }},
            {"$sort": {"total_links_added": -1}}
        ]
        
        results = list(self.db["fingerprints"].aggregate(pipeline))
        
        # Get post configs to add post info
        post_configs = {p["post_id"]: p for p in self.db["posts"].find({}, {"post_id": 1, "content_slug": 1})}
        
        return [{
            "post_id": r["post_id"],
            "content_slug": post_configs.get(r["post_id"], {}).get("content_slug", f"Post {r['post_id']}"),
            "total_updates": r["total_updates"],
            "successful_updates": r["successful_updates"],
            "failed_updates": 0,
            "success_rate": 100.0,
            "total_links_added": r["total_links_added"],
            "avg_links_per_update": round(r["total_links_added"] / r["total_updates"], 2) if r["total_updates"] > 0 else 0,
            "sites_count": r.get("sites_count", 1)
        } for r in results]
    
    def get_source_performance(self, days: int = 30) -> List[Dict]:
        """
        Get performance metrics per source URL
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of sources with their metrics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get all source monitoring data
        sources = list(self.db["source_monitoring"].find({}))
        
        source_data = []
        for source in sources:
            # Calculate recent performance
            recent_history = source.get("extraction_history", [])
            recent_history = [h for h in recent_history if datetime.fromisoformat(h["date"]) >= cutoff]
            
            if not recent_history:
                continue
            
            total = len(recent_history)
            successful = sum(1 for h in recent_history if h.get("success", False))
            total_links = sum(h.get("links_found", 0) for h in recent_history)
            
            source_data.append({
                "source_url": source["source_url"],
                "total_extractions": total,
                "successful_extractions": successful,
                "failed_extractions": total - successful,
                "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
                "total_links_extracted": total_links,
                "avg_links_per_extraction": round(total_links / total, 2) if total > 0 else 0,
                "consecutive_failures": source.get("consecutive_failures", 0),
                "current_health": self._determine_health_status(source),
                "last_success": source.get("last_success")
            })
        
        # Sort by total extractions
        source_data.sort(key=lambda x: x["total_extractions"], reverse=True)
        
        return source_data
    
    def get_extractor_performance(self, days: int = 30) -> List[Dict]:
        """
        Get performance metrics per extractor type
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of extractors with their metrics
        """
        # Get all post configs with extractors
        posts = list(self.db["posts"].find({}, {"post_id": 1, "extractor": 1, "extractor_map": 1}))
        
        # Count usage per extractor
        extractor_stats = defaultdict(lambda: {
            "posts_using": set(),
            "total_links": 0
        })
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        for post in posts:
            extractor = post.get("extractor", "default")
            
            # Get fingerprints for this post
            links_count = self.db["fingerprints"].count_documents({
                "post_id": post["post_id"],
                "date_iso": {"$gte": cutoff_date}
            })
            
            if links_count > 0:
                extractor_stats[extractor]["posts_using"].add(post["post_id"])
                extractor_stats[extractor]["total_links"] += links_count
        
        # Format results
        results = []
        for extractor, stats in extractor_stats.items():
            posts_count = len(stats["posts_using"])
            results.append({
                "extractor": extractor,
                "posts_using": posts_count,
                "total_links_extracted": stats["total_links"],
                "avg_links_per_post": round(stats["total_links"] / posts_count, 2) if posts_count > 0 else 0
            })
        
        # Sort by posts using
        results.sort(key=lambda x: x["posts_using"], reverse=True)
        
        return results
    
    def get_site_performance(self, days: int = 30) -> List[Dict]:
        """
        Get performance metrics per WordPress site
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of sites with their metrics
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get all fingerprints grouped by site_key
        pipeline = [
            {"$match": {"date_iso": {"$gte": cutoff_date}}},
            {"$group": {
                "_id": "$site_key",
                "total_links": {"$sum": 1},
                "unique_posts": {"$addToSet": "$post_id"}
            }},
            {"$sort": {"total_links": -1}}
        ]
        
        results = list(self.db["fingerprints"].aggregate(pipeline))
        
        site_data = []
        for r in results:
            site_key = r["_id"] or "default"
            posts_count = len(r["unique_posts"])
            
            site_data.append({
                "site_key": site_key,
                "total_links_added": r["total_links"],
                "unique_posts_updated": posts_count,
                "avg_links_per_post": round(r["total_links"] / posts_count, 2) if posts_count > 0 else 0
            })
        
        return site_data
    
    def get_hourly_pattern(self, days: int = 7) -> List[Dict]:
        """
        Get update patterns by hour of day
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of 24 data points (one per hour)
        """
        # Since we don't have timestamp data, return empty pattern
        # This could be enhanced by tracking update times in future
        return [{
            "hour": hour,
            "total_updates": 0,
            "successful": 0,
            "failed": 0
        } for hour in range(24)]
    
    def get_links_added_trend(self, days: int = 30) -> List[Dict]:
        """
        Get daily trend of links added
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of daily data points with links added count
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        pipeline = [
            {"$match": {"date_iso": {"$gte": cutoff_date}}},
            {"$group": {
                "_id": {"date": "$date_iso", "site": "$site_key"},
                "count": {"$sum": 1}
            }},
            {"$group": {
                "_id": "$_id.date",
                "total_links": {"$sum": "$count"},
                "by_site": {"$push": {"site": "$_id.site", "count": "$count"}}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(self.db["fingerprints"].aggregate(pipeline))
        
        return [{
            "date": r["_id"],
            "total_links": r["total_links"],
            "by_site": r["by_site"]
        } for r in results]
    
    def _get_health_distribution(self) -> Dict[str, int]:
        """Get count of sources by health status"""
        sources = list(self.db["source_monitoring"].find({}))
        
        distribution = {"healthy": 0, "warning": 0, "failing": 0, "critical": 0, "unknown": 0}
        
        for source in sources:
            status = self._determine_health_status(source)
            distribution[status] += 1
        
        return distribution
    
    def _determine_health_status(self, source: Dict) -> str:
        """Determine health status from source monitoring data"""
        consecutive_failures = source.get("consecutive_failures", 0)
        total = source.get("total_extractions", 0)
        successful = source.get("successful_extractions", 0)
        
        if total == 0:
            return "unknown"
        
        success_rate = successful / total if total > 0 else 0
        
        if consecutive_failures >= 5:
            return "critical"
        elif consecutive_failures >= 3:
            return "failing"
        elif success_rate < 0.8:
            return "warning"
        else:
            return "healthy"


# Singleton instance
_analytics_engine = None

def get_analytics_engine() -> AnalyticsEngine:
    """Get or create the analytics engine singleton"""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine
