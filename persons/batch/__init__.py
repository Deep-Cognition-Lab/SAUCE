from __future__ import annotations
from typing import Type
from functools import cache
from .batch_person import BatchedPerson
from .batch_hugging_face import PersonHuggingFace


@cache
def get_batch_dict() -> dict[str, Type[BatchedPerson]]:
    return {
        "batch" + PersonHuggingFace.PERSON_TYPE: PersonHuggingFace
    }
