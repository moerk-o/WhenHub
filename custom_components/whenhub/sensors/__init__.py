"""Sensor module for WhenHub integration.

This module exports the sensor classes for all WhenHub event types:
- TripSensor: Multi-day events with start and end dates
- MilestoneSensor: One-time events with a single target date
- AnniversarySensor: Recurring yearly events
- SpecialEventSensor: Holidays and astronomical events

Each sensor class inherits from BaseCountdownSensor and provides
event-specific calculations and attributes.
"""
from .trip import TripSensor
from .milestone import MilestoneSensor
from .anniversary import AnniversarySensor
from .special import SpecialEventSensor

__all__ = ["TripSensor", "MilestoneSensor", "AnniversarySensor", "SpecialEventSensor"]