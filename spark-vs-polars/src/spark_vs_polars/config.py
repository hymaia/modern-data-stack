import os
from dataclasses import dataclass, field


@dataclass
class Config:
    INPUT_FILE: str = field(default_factory=lambda: os.environ["INPUT_FILE"])
    OUTPUT_FILE: str = field(default_factory=lambda: os.environ["OUTPUT_FILE"])
