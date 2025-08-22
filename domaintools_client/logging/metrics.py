"""Metrics collection and monitoring utilities."""

import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class MetricValue:
    """Container for a metric value with timestamp."""

    value: Union[int, float]
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Performance statistics container."""

    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0

    def update(self, duration: float) -> None:
        """Update statistics with new duration."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.count


class MetricsCollector:
    """Thread-safe metrics collector."""

    def __init__(self, max_history: int = 1000):
        """Initialize metrics collector.

        Args:
            max_history: Maximum number of historical values to keep
        """
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._performance: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._lock = Lock()

    def record_counter(
        self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric.

        Args:
            name: Metric name
            value: Counter increment value
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            self._metrics[key].append(MetricValue(self._counters[key], labels=labels or {}))

    def record_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            self._metrics[key].append(MetricValue(value, labels=labels or {}))

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric.

        Args:
            name: Metric name
            value: Measurement value
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._metrics[key].append(MetricValue(value, labels=labels or {}))

    def record_performance(self, name: str, duration: float) -> None:
        """Record performance timing.

        Args:
            name: Operation name
            duration: Duration in seconds
        """
        with self._lock:
            self._performance[name].update(duration)

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value.

        Args:
            name: Metric name
            labels: Optional labels for the metric

        Returns:
            Current counter value
        """
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value.

        Args:
            name: Metric name
            labels: Optional labels for the metric

        Returns:
            Current gauge value
        """
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_histogram_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Get histogram statistics.

        Args:
            name: Metric name
            labels: Optional labels for the metric

        Returns:
            Dictionary with histogram statistics
        """
        key = self._make_key(name, labels)
        values = [m.value for m in self._metrics.get(key, [])]

        if not values:
            return {}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "p90": self._percentile(values, 0.9),
            "p95": self._percentile(values, 0.95),
            "p99": self._percentile(values, 0.99),
        }

    def get_performance_stats(self, name: str) -> Optional[PerformanceStats]:
        """Get performance statistics.

        Args:
            name: Operation name

        Returns:
            Performance statistics or None if not found
        """
        return self._performance.get(name)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics.

        Returns:
            Dictionary with all metrics
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name.split("|")[0], self._parse_labels(name))
                    for name in self._metrics.keys()
                },
                "performance": {
                    name: {
                        "count": stats.count,
                        "total_time": stats.total_time,
                        "min_time": stats.min_time if stats.min_time != float("inf") else 0.0,
                        "max_time": stats.max_time,
                        "avg_time": stats.avg_time,
                    }
                    for name, stats in self._performance.items()
                },
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._performance.clear()
            self._counters.clear()
            self._gauges.clear()

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a key for storing metrics with labels."""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}|{label_str}"

    def _parse_labels(self, key: str) -> Optional[Dict[str, str]]:
        """Parse labels from a metric key."""
        if "|" not in key:
            return None

        _, label_str = key.split("|", 1)
        labels = {}
        for pair in label_str.split(","):
            k, v = pair.split("=", 1)
            labels[k] = v
        return labels

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile
        f = int(k)
        c = f + 1
        if f == c:
            return sorted_values[f]
        return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def track_performance(operation_name: str) -> Callable[[F], F]:
    """Decorator to track function performance metrics.

    Args:
        operation_name: Name of the operation for metrics

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                # Record request counter
                _metrics_collector.record_counter(
                    f"{operation_name}_requests_total", labels={"function": func.__name__}
                )

                result = func(*args, **kwargs)

                # Record success counter
                _metrics_collector.record_counter(
                    f"{operation_name}_requests_success", labels={"function": func.__name__}
                )

                return result

            except Exception as e:
                # Record error counter
                _metrics_collector.record_counter(
                    f"{operation_name}_requests_error",
                    labels={"function": func.__name__, "error_type": type(e).__name__},
                )
                raise

            finally:
                # Record timing
                duration = time.time() - start_time
                _metrics_collector.record_histogram(
                    f"{operation_name}_duration_seconds",
                    duration,
                    labels={"function": func.__name__},
                )
                _metrics_collector.record_performance(operation_name, duration)

        return wrapper  # type: ignore[return-value]

    return decorator


def increment_counter(name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
    """Increment a counter metric.

    Args:
        name: Metric name
        value: Increment value
        labels: Optional labels
    """
    _metrics_collector.record_counter(name, value, labels)


def set_gauge(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Set a gauge metric value.

    Args:
        name: Metric name
        value: Gauge value
        labels: Optional labels
    """
    _metrics_collector.record_gauge(name, value, labels)


def observe_histogram(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Observe a value in a histogram metric.

    Args:
        name: Metric name
        value: Observed value
        labels: Optional labels
    """
    _metrics_collector.record_histogram(name, value, labels)
