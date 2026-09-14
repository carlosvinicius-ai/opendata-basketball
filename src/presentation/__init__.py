"""Presentation layer: CLI commands, static chart visualizers, and HTML report generators."""

from presentation.charts_generator import ChartsGenerator
from presentation.cli import main
from presentation.report_builder import ReportBuilder

__all__ = [
    "main",
    "ReportBuilder",
    "ChartsGenerator",
]
