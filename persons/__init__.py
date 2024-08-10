from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

from typing import Type
from functools import cache

from dotenv import load_dotenv

import persons.fake_person
import persons.person
import persons.human
import persons.person_gpt3_5
import persons.person_openai_completion
import persons.person_hugging_face
import persons.asynchronous_persons.async_human
import persons.asynchronous_persons.experimental_example_persons.first_decides_then_generates as f_d_t_g
import persons.asynchronous_persons.experimental_example_persons.first_generates_then_decides as f_g_t_d
import persons.asynchronous_persons.experimental_example_persons.asynchronous_group_discussant as ph_d
import persons.batch.batch_person
from .batch import get_batch_dict

load_dotenv()


@cache  # adding cache avoid creating the dict again and again, but still make it read only
def __generate_person_dict():
    return {
        persons.fake_person.FakePerson.PERSON_TYPE: persons.fake_person.FakePerson,
        persons.human.Human.PERSON_TYPE: persons.human.Human,
        persons.person_gpt3_5.Person3_5.PERSON_TYPE: persons.person_gpt3_5.Person3_5,
        persons.person_openai_completion.PersonOpenAiCompletion.PERSON_TYPE: persons.person_openai_completion.PersonOpenAiCompletion,
        persons.person_hugging_face.PersonHuggingFace.PERSON_TYPE:  persons.person_hugging_face.PersonHuggingFace,
        persons.asynchronous_persons.async_human.AsynchronousHuman.PERSON_TYPE: persons.asynchronous_persons.async_human.AsynchronousHuman,
        f_d_t_g.FirstDecidesThenGenerates.PERSON_TYPE: f_d_t_g.FirstDecidesThenGenerates,
        f_g_t_d.FirstGeneratesThenDecides.PERSON_TYPE: f_g_t_d.FirstGeneratesThenDecides,
        ph_d.AsynchronousGroupDiscussant.PERSON_TYPE: ph_d.AsynchronousGroupDiscussant,
        **get_batch_dict(),
    }


@cache # reduce the loading time the user was already reloaded
def get_person_class(name: str) -> Type[persons.person.Person]:
    _dict = __generate_person_dict()
    return _dict.get(name)
