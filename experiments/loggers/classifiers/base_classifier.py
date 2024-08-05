import logging
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseClassifier(ABC):
    NAME = "BASE"

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def classify(self, to_classify: Any, *args, **kwargs) -> Optional[dict]:
        raise NotImplementedError()


