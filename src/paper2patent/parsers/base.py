"""Abstract base class for paper parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from paper2patent.ir import PaperIR


class BaseParser(ABC):
    """All parsers convert an input path to a PaperIR."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    @abstractmethod
    def parse(self, input_path: str) -> PaperIR:
        """Parse the input and return a PaperIR."""
        ...
