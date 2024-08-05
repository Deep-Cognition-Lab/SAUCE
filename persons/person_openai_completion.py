""" 
This file contains a Person implementation which utilises the OpenAI Completion API.
API documentation - https://platform.openai.com/docs/api-reference/completions/create.
"""

from __future__ import annotations
import warnings
import os
import openai

from persons.person import Person

# Protect cyclic imports caused from typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_rooms.ChatEntry import ChatEntry



class PersonOpenAiCompletion(Person):
    PERSON_TYPE = "person_openai_completion"
    MODEL_NAME = "text-davinci-003"

    def __init__(self, background_story: str, name: str, *args, **kwargs):
        super().__init__(background_story, name)
        # Set up your OpenAI API credentials.
        openai.api_key = os.environ.get("OPENAI_API_KEY", "")
        openai.organization = os.environ.get("OPENAI_ORG_ID")  # TODO remove default?
        warnings.warn("This API has been deprecated by OpenAI")

        self.model_name = PersonOpenAiCompletion.MODEL_NAME

    def generate_answer(self, experiment_scenario: str, chat_list: List[ChatEntry]):
        generated_prompt: str = self.create_prompt(experiment_scenario, chat_list)
        full_response = openai.Completion.create(
            model=self.model_name,
            prompt=generated_prompt,
            max_tokens=100,  # Limit the response length to 100 tokens.
            n=1,  # Generate a single response.
            temperature=0.6,  # Control the randomness of the output.
        )

        # Retrieve the generated response
        chat_answer: str = full_response.choices[0].text
        return ChatEntry(entity=self, prompt=generated_prompt, answer=chat_answer)

    def create_prompt(self, experiment_scenario: str, chat_list: List[ChatEntry]) -> str:
        """ 
        Creates a prompt with the past conversation formatted as a string.
        """
        output = ("Instructions: \n"
                  f"Your name is {self.name}. \n"
                  f"The scenario is the following: {experiment_scenario}\n"
                  f"This is your background story: {self.background_story}\n\n"
                  "The following is a conversation between you and other speakers. Complete "
                  "your next reply (starting with 'Me:'). Try to keep the reply shorter than "
                  "30 words.\n\n")

        for chat_entry in chat_list:
            cur_person = chat_entry.entity
            current_name = "Me" if cur_person is self else cur_person.name
            output += f"{current_name}: {chat_entry.answer}\n"
            output += f"###################################\n"

        output += "Me: "
        return output
