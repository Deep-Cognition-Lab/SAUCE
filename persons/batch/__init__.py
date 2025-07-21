from __future__ import annotations
from typing import Type
from functools import cache
from .batch_person import BatchedPerson
from .batch_hugging_face import PersonHuggingFace
from .batch_gpt_4 import BatchedPerson4_0


@cache
def get_batch_dict() -> dict[str, Type[BatchedPerson]]:
    return {
        "batch" + PersonHuggingFace.PERSON_TYPE: PersonHuggingFace,
        "batch" + BatchedPerson4_0.PERSON_TYPE: BatchedPerson4_0,  # Add mapping for BatchedPerson4_0
    }