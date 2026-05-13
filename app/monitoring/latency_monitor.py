"""
Kenya-Optimized Latency Monitor
Tracks network latency and provides VPS-mode recommendations
Monitors both cTrader and MT5 connectivity
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics


class ConnectionQuality(Enum):
    """Network connection quality assessment"""
    EXCELLENT = "excellent"  # < 50ms
    GOOD = "good"  # 50-100ms
    FAIR = "fair"  # 100-200ms
    POOR = "poor"  # > 200ms


@dataclass
class LatencyMeasurement:
    """Single latency measurement"""
    timestamp: datetime
    server: str
    latency_ms: float
    quality: ConnectionQuality
    is_vps_recommended: bool = False


@dataclass
class LatencyStats:
    """Latency statistics for a period"""
    server: str
    sample_count: int
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    median_latency_ms: float = 0.0
    std_dev_ms: float = 0.0
    quality: ConnectionQuality = ConnectionQuality.FAIR
    vps_recommended: bool = False
    measurement_period_seconds: int = 0


class LatencyMonitor:
    """
    Monitors network latency to trading servers
    Provides recommendations for VPS-hosted mode in Kenya
    """
    
    # Latency thresholds (ms)
    LATENCY_THRESHOLD_VPS = 200.0  # Suggest VPS if > 200ms
    LATENCY_THRESHOLD_WARNING = 150.0  # Warning if > 150ms
    
    # Servers to monitor
    SERVERS = {
        "ctrader": "https://ctrader-api.example.com",  # Placeholder
        "exness_ke": "mt5.exnesskenya.com",
        "maven": "maven.broker.example.com",
    }
    
    # Measurement config
    MEASUREMENT_INTERVAL_SECONDS = 60  # Measure every 60s
    HISTORY_WINDOW_SECONDS = 300  # Keep 5min history
    MIN_SAMPLES_FOR_STATS = 5
    
    def __init__(self):
        self.measurements: List[LatencyMeasurement] = []
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.vps_mode_enabled = False
        self.last_recommendation_time: Optional[datetime] = None
    
    async def start_monitoring(self) -> None:
        """Start background latency monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self.is_running = False
        if self.monitor_task:
            await self.monitor_task
    
    async def _monitor_loop(self) -> None:
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Measure latency to each server
                tasks = [
                    self.measure_latency(server, url)
                    for server, url in self.SERVERS.items()
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check if VPS mode should be recommended
                await self._check_vps_recommendation()
                
                # Cleanup old measurements
                self._cleanup_old_measurements()
                
                # Wait before next measurement
                await asyncio.sleep(self.MEASUREMENT_INTERVAL_SECONDS)
            
            except Exception as e:
                await asyncio.sleep(self.MEASUREMENT_INTERVAL_SECONDS)
    
    async def measure_latency(self, server: str, url: Optional[str] = None) -> float:
        """
        Measure latency to server
        Returns latency in milliseconds
        """
        try:
            start = time.perf_counter()
            
            # Simulate latency measurement (in real implementation, ping or HTTP request)
            # For now, this would be replaced with actual network requests
            await asyncio.sleep(0.01)  # Placeholder
            
            latency_ms = (time.perf_counter() - start) * 1000
            
            # Determine quality
            if latency_ms < 50:
                quality = ConnectionQuality.EXCELLENT
            elif latency_ms < 100:
                quality = ConnectionQuality.GOOD
            elif latency_ms < 200:
                quality = ConnectionQuality.FAIR
            else:
                quality = ConnectionQuality.POOR
            
            # Create measurement
            measurement = LatencyMeasurement(
                timestamp=datetime.now(),
                server=server,
                latency_ms=latency_ms,
                quality=quality,
                is_vps_recommended=latency_ms > self.LATENCY_THRESHOLD_VPS,
            )
            
            self.measurements.append(measurement)
            return latency_ms
        
        except Exception as e:
            return -1.0
    
    def get_current_stats(self, server: Optional[str] = None, window_seconds: Optional[int] = None) -> Dict[str, LatencyStats]:
        """
        Get latency statistics
        
        Args:
            server: Specific server to get stats for (None = all)
            window_seconds: Time window for stats (None = use default)
        
        Returns:
            dict of server -> LatencyStats
        """
        if window_seconds is None:
            window_seconds = self.HISTORY_WINDOW_SECONDS
        
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        recent = [m for m in self.measurements if m.timestamp > cutoff_time]
        
        # Group by server
        by_server: Dict[str, List[LatencyMeasurement]] = {}
        for m in recent:
            if server and m.server != server:
                continue
            if m.server not in by_server:
                by_server[m.server] = []
            by_server[m.server].append(m)
        
        # Calculate stats
        stats_dict: Dict[str, LatencyStats] = {}
        for srv, measurements in by_server.items():
            if len(measurements) >= self.MIN_SAMPLES_FOR_STATS:
                latencies = [m.latency_ms for m in measurements if m.latency_ms > 0]
                
                stats_dict[srv] = LatencyStats(
                    server=srv,
                    sample_count=len(latencies),
                    min_latency_ms=min(latencies),
                    max_latency_ms=max(latencies),
                    avg_latency_ms=statistics.mean(latencies),
                    median_latency_ms=statistics.median(latencies),
                    std_dev_ms=statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
                    quality=self._assess_quality(statistics.mean(latencies)),
                    vps_recommended=statistics.mean(latencies) > self.LATENCY_THRESHOLD_VPS,
                    measurement_period_seconds=window_seconds,
                )
        
        return stats_dict
    
    def _assess_quality(self, avg_latency_ms: float) -> ConnectionQuality:
        """Assess connection quality from average latency"""
        if avg_latency_ms < 50:
            return ConnectionQuality.EXCELLENT
        elif avg_latency_ms < 100:
            return ConnectionQuality.GOOD
        elif avg_latency_ms < 200:
            return ConnectionQuality.FAIR
        else:
            return ConnectionQuality.POOR
    
    async def _check_vps_recommendation(self) -> None:
        """Check if VPS mode should be recommended"""
        stats = self.get_current_stats()
        
        should_recommend_vps = any(s.vps_recommended for s in stats.values())
        
        if should_recommend_vps and not self.vps_mode_enabled:
            self.last_recommendation_time = datetime.now()
    
    def _cleanup_old_measurements(self) -> None:
        """Remove measurements older than history window"""
        cutoff_time = datetime.now() - timedelta(seconds=self.HISTORY_WINDOW_SECONDS * 2)
        self.measurements = [m for m in self.measurements if m.timestamp > cutoff_time]
    
    def should_use_vps_mode(self) -> bool:
        """
        Determine if VPS mode should be used
        Kenya-specific optimization: if latency > 200ms to servers
        """
        stats = self.get_current_stats()
        
        if not stats:
            return False
        
        # If any server has high latency, recommend VPS
        return any(s.vps_recommended for s in stats.values())
    
    def get_recommendations(self) -> Dict[str, str]:
        """Get actionable recommendations for the user"""
        stats = self.get_current_stats()
        recommendations = {}
        
        for srv, stat in stats.items():
            if stat.quality == ConnectionQuality.POOR:
                recommendations[srv] = (
                    f"⚠️ POOR connectivity to {srv} ({stat.avg_latency_ms:.0f}ms avg). "
                    f"Consider enabling VPS-Hosted Mode for better execution reliability."
                )
            elif stat.quality == ConnectionQuality.FAIR:
                recommendations[srv] = (
                    f"⚠️ Fair connectivity to {srv} ({stat.avg_latency_ms:.0f}ms avg). "
                    f"Monitor performance; VPS mode recommended if degrading."
                )
            elif stat.quality == ConnectionQuality.GOOD:
                recommendations[srv] = (
                    f"✓ Good connectivity to {srv} ({stat.avg_latency_ms:.0f}ms avg). "
                    f"Direct execution is acceptable."
                )
            else:  # EXCELLENT
                recommendations[srv] = (
                    f"✓ Excellent connectivity to {srv} ({stat.avg_latency_ms:.0f}ms avg). "
                    f"Optimal for direct execution."
                )
        
        return recommendations
    
    def get_status_display(self) -> Dict[str, str]:
        """Get formatted status for UI display"""
        stats = self.get_current_stats()
        
        if not stats:
            return {"status": "No data collected yet"}
        
        status = {}
        for srv, stat in stats.items():
            status[srv] = (
                f"{stat.quality.value.upper()} | "
                f"Avg: {stat.avg_latency_ms:.0f}ms | "
                f"Min: {stat.min_latency_ms:.0f}ms | "
                f"Max: {stat.max_latency_ms:.0f}ms"
            )
        
        status["vps_recommended"] = "Yes ⚠️" if self.should_use_vps_mode() else "No ✓"
        
        return status
