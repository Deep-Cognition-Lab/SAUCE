from __future__ import annotations
import logging
import threading
from typing import List, Optional, TYPE_CHECKING
import pandas as pd
from experiments.loggers.classifiers import BaseClassifier


class OurLogger(logging.Logger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def makeRecord(self, *args, **kwargs) -> logging.LogRecord:
        record = super().makeRecord(*args, **kwargs)
        try:
            extra = args[8]
        except IndexError:
            extra = {}
        if not extra:
            extra = kwargs.get("extra", {})
        record.__dict__['kwargs'] = extra
        return record


class CsvFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self.__classifier: Optional[List[BaseClassifier]] = None
        self.__classifier_lock = threading.RLock()

    @property
    def classifiers(self):
        with self.__classifier_lock:
            return self.__classifier

    @classifiers.setter
    def classifiers(self, v: List[BaseClassifier]):
        if not isinstance(v, list):
            raise TypeError("Only list of BaseClassifier")
        tmp = []
        with self.__classifier_lock:
            for classifier in v:
                if isinstance(classifier, BaseClassifier):
                    tmp(v)
            self.__classifier = tmp

    def add_classifier(self, classifier: BaseClassifier):
        with self.__classifier_lock:
            if isinstance(classifier, BaseClassifier):
                self.__classifier.append(classifier)

    def emit(self, record):
        try:
            log_data = {
                **record.__dict__,
                'Level': record.levelname,
                'Message': record.msg,
                'Timestamp': record.created,
            }

            if hasattr(record,"kwargs"):
                log_data.update(record.kwargs)
                if record.kwargs.get('do_classify', False) and record.kwargs.get('classify'):
                    self.classify(log_data)
            df = pd.DataFrame([log_data])
            df.to_json(self.baseFilename, mode='a', lines=True, orient="records")

        except Exception:
            self.handleError(record)

    def classify(self, log_data):
        # Classification logic goes here
        # Modify the log_data dictionary based on classification results
        # For example, add a 'Classification' key-value pair
        if not self.classifiers or len(self.classifiers) == 0:
            print("Unable run it")
            return
        threads: List[threading.Thread] = []
        for classifier in self.classifiers:
            threads.append(
                threading.Thread(target=lambda: log_data.update(classifier.classify(log_data.get('classify'))))
            )
            threads[-1].start()
        [t.join() for t in threads]

    def fileExists(self):
        # Check if the file already exists
        try:
            with open(self.baseFilename, 'r') as file:
                return bool(file.readlines())
        except FileNotFoundError:
            return False


class ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            log_entry = self.format(record)

            # Include kwargs in the log message
            if hasattr(record, "kwargs"):
                strip = lambda a: str(a).strip().rstrip(str('\n'))
                kwargs_str = " ".join([f"{strip(key)}= {strip(value)}" for key, value in record.kwargs.items()])
                log_entry += f"\n{kwargs_str=}"
            print(log_entry)
        except Exception:
            self.handleError(record)
