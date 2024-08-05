""" 
This file contains a Person implementation for loading HuggingFace models.

Currently we only support models which follow the Alpaca prompt format:
    ### Instruction:
    {instruction}

    ### Input:
    {input}

    ### Response:
More information at github.com/tatsu-lab/stanford_alpaca#data-release

Important: This class loads the model locally and might require high system resources
    (in particular high GPU vRAM).
"""

from __future__ import annotations

import copy
import logging
from typing import Callable

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig, BitsAndBytesConfig
from termcolor import colored
import gc

# Protect cyclic imports caused from typing

from persons.person import Person
from session_rooms.session_room import ChatEntry


log = logging.getLogger(__name__)

# Load each model only once to save expensive memory.
_hf_cache = {}


def cache_or_init(key: str, init_func: Callable):
    """
    Returns the model from the cache if available.
    Otherwise, initializes it with the given init_func.
    """
    if key not in _hf_cache:
        logging.debug(f"loading {key}")
        _hf_cache[key] = init_func()
    return _hf_cache[key]


class PersonHuggingFace(Person):
    PERSON_TYPE = "person_hugging_face"

    def __init__(self, background_story: str, name: str, *args, **kwargs):
        """ Loads the model into GPU / Memory. This might take a few minutes. """
        super().__init__(background_story, name)
        model_path = kwargs.get("model_path", "microsoft/Phi-3-mini-4k-instruct")  # 13B.
        tokenizer_weights = model_path
        model_weights = model_path
        adapters_weights = ""

        self.tokenizer = cache_or_init(
            key=f"{tokenizer_weights}_tokenizer",
            # Use_fast=False? https://huggingface.co/openlm-research/open_llama_13b
            init_func=lambda: AutoTokenizer.from_pretrained(tokenizer_weights))
        self.model = cache_or_init(
            key=f"{model_weights}_model",
            init_func=lambda: AutoModelForCausalLM.from_pretrained(
                model_weights, device_map="auto",
                # quantization_config=BitsAndBytesConfig(
                #     load_in_4bit=True,
                #     bnb_4bit_use_double_quant=True,
                #     bnb_4bit_quant_type="nf4",
                #     bnb_4bit_compute_dtype=torch.bfloat16),
                trust_remote_code=True  # TODO - maybe remove, new addition to check bugs
            ))
        log.debug("finish loading model before breaking point! yay!")
        # self.model.tie_weights()? - https://paperswithcode.com/method/weight-tying

        if adapters_weights:
            # If there are separate adapter weights add them to the underlying model.
            self.model = cache_or_init(
                key=f"{adapters_weights}_adapters",
                init_func=lambda: AutoTokenizer.from_pretrained(
                    adapters_weights, self.model))

    def generate_answer(self, experiment_scenario: str, chat_list: list[ChatEntry]):
        prompt: str = self.create_prompt(experiment_scenario, chat_list)
        config = GenerationConfig(
            # TODO - consider using repetition_penalty.
            do_sample=True,
            temperature=1.0,
            top_p=0.9,
            num_beams=1,  # Increase once there is more memory.
            use_cache=True,  # True for speedup, False only if reaching memory limit.
            max_new_tokens=100
        )
        answer = self.evaluate(config, prompt, use_cuda=torch.cuda.is_available())
        return ChatEntry(entity=self, prompt=prompt, answer=answer)

    def evaluate(self, generation_config: GenerationConfig, prompt: str,
                 use_cuda, max_new_tokens=50):
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        if use_cuda:
            input_ids = input_ids.cuda()

        generation_output = self.model.generate(
            input_ids=input_ids,
            generation_config=generation_config,
            return_dict_in_generate=True,
            output_scores=True,
            max_new_tokens=max_new_tokens
        )
        # Clear expensive GPU memory.
        del input_ids
        gc.collect()

        assert len(generation_output.sequences) == 1  # TODO: when can be more than 1?
        output = self.tokenizer.decode(generation_output.sequences[0])
        # print(colored(output, "red"))

        # The model returns the new tokens concatenated to the input prompt.
        # Only take the new tokens which is after "### Response:":
        # Also, strip the part which is after the  EOS token ("</s>").
        output = output.split("### Response:")[1]
        output = output.strip().split("</s>")[0].split("\n")[0]
        return output.strip().removeprefix("Me: ")

    def create_prompt(self, experiment_scenario: str, chat_list: list[ChatEntry]) -> str:
        """ 
        Creates a prompt with the past conversation formatted as a string.
        """
        output = ("### Instruction: \n"
                  f"Your name is {self.name}. \n"
                  f"This is your background story: {self.background_story}.\n"
                  f"The following is a {experiment_scenario}. "
                  "Complete your next reply (starting with 'Me:'). "
                  "Try to keep your reply shorter than 30 words.\n\n"
                  "### Input:\n")

        for chat_entry in chat_list:
            cur_name = chat_entry.entity.name
            current_name = "Me" if cur_name == self.name else cur_name
            output += f"{current_name}: {chat_entry.answer}\n"

        output += "### Response:\nMe:"
        return output
