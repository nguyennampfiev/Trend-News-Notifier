import logging
import time

import psutil
import torch
from fastapi import Request
from opentelemetry.metrics import Observation, get_meter_provider
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Logs latency, CPU, RAM per HTTP request for Grafana."""

    def __init__(self, app):
        super().__init__(app)
        meter = get_meter_provider().get_meter("trend-news-metrics")

        self.http_latency = meter.create_histogram(
            name="http.request.latency",
            description="HTTP request latency (seconds)",
            unit="s",
        )

        self.cpu_gauge = meter.create_observable_gauge(
            name="http.request.cpu",
            description="CPU percent during HTTP request",
            unit="percent",
            callbacks=[self._cpu_callback],
        )
        self.ram_gauge = meter.create_observable_gauge(
            name="http.request.ram",
            description="RAM percent during HTTP request",
            unit="percent",
            callbacks=[self._ram_callback],
        )
        self.gpu_gauge = meter.create_observable_gauge(
            name="http.request.gpu",
            description="GPU percent during HTTP request",
            unit="percent",
            callbacks=[self._gpu_callback],
        )
        self._current_cpu = 0.0
        self._current_ram = 0.0
        self._current_gpu = (
            torch.cuda.utilization(0) if torch.cuda.is_available() else 0.0
        )

    def _cpu_callback(self, options):
        return [Observation(self._current_cpu)]

    def _ram_callback(self, options):
        return [Observation(self._current_ram)]

    def _gpu_callback(self, options):
        return [Observation(self._current_gpu)]

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            end = time.perf_counter()
            latency = end - start
            self._current_cpu = psutil.cpu_percent(interval=0.1)
            self._current_ram = psutil.virtual_memory().percent
            self._current_gpu = (
                torch.cuda.utilization(0) if torch.cuda.is_available() else 0.0
            )
            self.http_latency.record(latency)
            logger.info(
                f"HTTP {request.method} {request.url.path} | "
                f"latency={latency:.3f}s | CPU={self._current_cpu:.1f}% | RAM={self._current_ram:.1f}% | GPU={self._current_gpu:.1f}%"
            )
