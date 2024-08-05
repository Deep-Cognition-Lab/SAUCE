import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Optional

from experiments.loggers.classifiers import BaseClassifier


class RegexClassifier(BaseClassifier):
    NAME = "Regex"

    def __init__(self, regex: str = None, *args, **kwargs):
        super().__init__(regex, *args, **kwargs)
        self.regex = kwargs.get("regex", regex)

    def classify(self, to_classify: Any, *args, **kwargs) -> Optional[dict]:
        if not self.regex:
            self.logger.info("No regex given")
        compiled_regex = re.compile(self.regex)
        result = compiled_regex.findall(to_classify)
        result_dict = {
            "regex": self.regex,
            "classify": to_classify
        }
        for index, apper in enumerate(result):
            result_dict[f'appearance {index}'] = apper
        return result_dict
