from __future__ import annotations

from typing import Type, TYPE_CHECKING

from session_rooms.ChatEntry import BatchChatList, ChatEntry
from .batch_person import BatchedPerson

if TYPE_CHECKING:
    from persons.person import Person


class AutoBatchPerson(BatchedPerson):
    def __init__(self,
                 background_stories: list[str],
                 names: list[str],
                 tag: str,
                 person_class: Type[Person],
                 person_kwargs: dict = None,
                 *args, **kwargs):
        super().__init__(background_stories, names, tag, )
        p_kwargs = person_kwargs.copy() if person_kwargs else {}
        self.persons_instances = [
            person_class(background_story=person_info[0], name=person_info[1], **{**kwargs, **p_kwargs, })
            for person_info in zip(self.background_stories, self.names)]

    def generate_answer(self, experiment_scenario: str, chat_lists: BatchChatList, *args, **kwargs) -> list[ChatEntry]:
        chat_entries = []
        for (person, chat_list) in zip(self.persons_instances, chat_lists):
            chat_entries.append(person.generate_answer(experiment_scenario, chat_list))
        return chat_entries
