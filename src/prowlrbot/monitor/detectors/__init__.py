# -*- coding: utf-8 -*-
from prowlrbot.monitor.detectors.base import BaseDetector, DetectionResult
from prowlrbot.monitor.detectors.web import WebDetector
from prowlrbot.monitor.detectors.api import APIDetector

__all__ = ["BaseDetector", "DetectionResult", "WebDetector", "APIDetector"]
