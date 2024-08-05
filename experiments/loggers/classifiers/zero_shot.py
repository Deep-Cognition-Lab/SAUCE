import warnings
from typing import Any, Optional

from .base_classifier import BaseClassifier

try:
    from transformers import pipeline, Pipeline
except Exception:
    warnings.warn("transformers not installed don't use classifier")


class ZeroShot(BaseClassifier):
    NAME = "ZeroShot"

    def __init__(self, model="facebook/bart-large-mnli", labels=[], *args, **kwargs):
        super().__init__(model, labels, *args, **kwargs)
        try:
            self.classifier: Optional[Pipeline] = pipeline("zero-shot-classification",
                                                           model=kwargs.get("model", model))
        except Exception as e:
            self.logger.exception("Unable to load classifier")
            self.classifier = None

        self.labels = kwargs.get("labels", labels)

    def classify(self, to_classify: Any, *args, **kwargs) -> Optional[dict]:
        if not self.classifier:
            self.logger.warning("No classifier")
            return
        if not isinstance(to_classify, str):
            self.logger.error(f"received {type(to_classify)} which is not str")
            return
        result = self.classifier(to_classify, self.labels)
        label_score_dict = dict(zip(result['labels'], result['scores']))
        max_index = max(range(len(result['scores'])), key=result['scores'].__getitem__)
        max_label = result['labels'][max_index]
        max_score = result['scores'][max_index]
        return {
            "max_label": max_label,
            "max_score": max_score,
            **label_score_dict
        }

