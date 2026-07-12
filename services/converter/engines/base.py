from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class ConversionRoute:
    category: str
    source: str
    target: str
    engine: str
    handler: Callable
    label: str = ""


@dataclass
class ConvertContext:
    job_id: str
    source: str
    target: str
    input_path: Path
    output_path: Path
    options: dict
    set_progress: Callable[[int, str], None]
