# -*- coding: utf-8 -*-
from prowlrbot.monitor.notifications.base import BaseNotifier
from prowlrbot.monitor.notifications.webhook import WebhookNotifier

__all__ = ["BaseNotifier", "WebhookNotifier"]
