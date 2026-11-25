"""Configuration for the document integrity screening pipeline."""

from dataclasses import dataclass


@dataclass
class Config:
    # Fixed development default; hold-out examples are not used for tuning.
    threshold: float = 0.60
    chunk_size: int = 300
    overlap: int = 45
    device: str = "cpu"
    batch_size: int = 32
    boilerplate_fraction: float = 0.5
    ai_medium: float = 0.65
    ai_high: float = 0.82
    risk_medium: float = 10.0
    risk_high: float = 25.0
