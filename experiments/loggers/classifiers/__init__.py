from typing import Type
from experiments.loggers.classifiers.base_classifier import BaseClassifier
from experiments.loggers.classifiers.zero_shot import ZeroShot
from experiments.loggers.classifiers.regex_classifier import RegexClassifier


def get_known_classifier(name: str) -> Type[BaseClassifier]:
    known_classifier = {
        BaseClassifier.NAME: BaseClassifier,
        ZeroShot.NAME: ZeroShot,
        RegexClassifier.NAME:RegexClassifier
    }
    return known_classifier.get(name)
