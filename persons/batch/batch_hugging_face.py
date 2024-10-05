"""
This file contains a Person implementation for loading HuggingFace models.

The main arguments are:
    * model_path: The path to the model to load.
    * prompt_type: The type of prompt to use. "mistral_instruct" / "llama_instruct".
    * background_story: The background story of the person.
    * name: The name of the person.

Important: This class loads the model locally and might require high system resources
    (in particular high GPU vRAM).
"""

from __future__ import annotations

import gc
from typing import Callable, TYPE_CHECKING

import torch
from termcolor import colored
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, GenerationConfig

from persons.batch.batch_person import BatchedPerson, InBatchPerson
from session_rooms.ChatEntry import BatchChatList, ChatEntry

if TYPE_CHECKING:
    pass
# Load each model only once to save expensive memory.
_hf_cache = {}


def cache_or_init(key: str, init_func: Callable):
    """
    Returns the model from the cache if available.
    Otherwise, initializes it with the given init_func.
    """
    if key not in _hf_cache:
        print(colored(f"loading {key}", "blue"))
        _hf_cache[key] = init_func()
    return _hf_cache[key]


def clear_cache():
    """ Clears the cache of all loaded models. """
    for model in _hf_cache.values(): del model
    _hf_cache.clear()
    gc.collect()
    torch.cuda.empty_cache()


class PersonHuggingFace(BatchedPerson):
    PERSON_TYPE = "PersonHuggingFace"

    def __init__(self, background_stories: list[str], names: list[str], tag: str = None, *args, **kwargs):
        super().__init__(background_stories, names, tag)
        # TODO change assertion to raise, since this input validation stuff
        model_path = kwargs.get("model_path")  # 13B.
        # assert "prompt_type" in kwargs
        self.prompt_type = kwargs.get("prompt_type",)

        if not model_path:
            raise ValueError("model path should not tbe none")
        if not self.prompt_type:
            raise ValueError("prompt type should not tbe none")

        self.confirmation_bias = kwargs["confirmation_bias"] if "confirmation_bias" in kwargs else None

        tokenizer_weights = model_path
        model_weights = model_path
        adapters_weights = ""

        self.tokenizer = cache_or_init(
            key=f"{tokenizer_weights}_tokenizer",
            # Use_fast=False? https://huggingface.co/openlm-research/open_llama_13b
            init_func=lambda: AutoTokenizer.from_pretrained(tokenizer_weights))
        # TODO: add flag to control quanitization.
        self.model = cache_or_init(
            key=f"{model_weights}_model",
            init_func=lambda: AutoModelForCausalLM.from_pretrained(
                model_weights, device_map="auto", quantization_config=BitsAndBytesConfig(
                    load_in_8bit=True, bnb_8bit_compute_dtype=torch.bfloat16)))
        # Padding is needed as we infer all the batch at once.
        self.model.config.pad_token_id = self.tokenizer.pad_token_id = self.tokenizer.unk_token_id
        self.tokenizer.padding_side = 'left'
        # self.model.tie_weights()? - https://paperswithcode.com/method/weight-tying

        if adapters_weights:
            # If there are separate adapter weights add them to the underlying model.
            self.model = cache_or_init(
                key=f"{adapters_weights}_adapters",
                init_func=lambda: AutoTokenizer.from_pretrained(
                    adapters_weights, self.model))

    #
    def generate_answer(self, experiment_scenario: str, chat_lists: BatchChatList, do_sample: bool = True,*args,**kwargs):
        assert len(chat_lists) == len(self.persons), (
            f"batch size {len(chat_lists)} of chat and persons {len(self.persons)} must match"
        )

        prompts: list[str] = [self.create_prompt(experiment_scenario, chat_list, person)
                              for chat_list, person in zip(chat_lists, self.persons)]
        config = GenerationConfig(
            # TODO - consider using repetition_penalty.
            do_sample=do_sample,
            temperature=1.0,
            top_p=0.9,
            num_beams=1,  # Increase once there is more memory.
            use_cache=True,  # True for speedup, False only if reaching memory limit.
            max_new_tokens=70,
            pad_token_id=self.model.config.pad_token_id,
        )
        answers = self.evaluate(config, prompts, use_cuda=torch.cuda.is_available())
        return [ChatEntry(entity=person, prompt=prompt, answer=answer)
                for prompt, answer, person in zip(prompts, answers, self.persons)]

    def evaluate(self, generation_config: GenerationConfig, prompts: list[str],
                 use_cuda, max_new_tokens=70):
        input_ids = self.tokenizer(prompts, return_tensors="pt", padding=True).input_ids
        if use_cuda:
            input_ids = input_ids.cuda()

        generation_output = self.model.generate(
            input_ids=input_ids,
            generation_config=generation_config,
            return_dict_in_generate=True,
            output_scores=True,
            max_new_tokens=max_new_tokens,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        # Clear expensive GPU memory.
        del input_ids
        gc.collect()

        outputs = [self.tokenizer.decode(seq) for seq in generation_output.sequences]
        # print(colored(prompts[0], "blue"))

        # The model returns the new tokens concatenated to the input prompt.
        # Only take the new tokens which is after "### Response:":
        # Also, strip the part which is after the  EOS token ("</s>").
        _, end_seq = self.get_stard_and_end_seq()
        return [output.split(end_seq)[1].strip().split("</s>")[0].split("\n")[0].strip()
                for output in outputs]

    def create_prompt(self, experiment_scenario: str, chat_list: list[ChatEntry],
                      self_person: InBatchPerson) -> str:
        if self.prompt_type in ["mistral_instruct", "llama_instruct"]:
            return self.create_instruct_prompt(experiment_scenario, chat_list, self_person)
        assert False, f"Unknown prompt type: {self.prompt_type}"

    def get_stard_and_end_seq(self):
        if self.prompt_type == "mistral_instruct":
            return "[INST] ", " [/INST] Me:"
        if self.prompt_type == "llama_instruct":
            return "### Instruction:\n", "\n\n### Response:\nMe:"
        assert False, f"Unknown prompt type: {self.prompt_type}"

    def create_instruct_prompt(self, experiment_scenario: str, chat_list: list[ChatEntry],
                               self_person: InBatchPerson) -> str:
        """
        Creates a prompt with the past conversation formatted as a string.
        The returned prompt is using an instructions tunning format. E.g.,:
        - Mistral prompt format: [INST] ... [/INST] <ai_response>
        - LLaMa prompt format: ### Instruction: ... ### Response: <ai_response>
        """
        start_seq, end_seq = self.get_stard_and_end_seq()
        output = f"{start_seq}"
        output += (f"Your name is {self_person.name}. Your background narrative is: {self_person.background_story}.\n\n"
                   f"Complete your next reply in the following {experiment_scenario}.\n"
                   "Your reply must be concise and realistically reflect your background narrative.\n\n")

        if self.confirmation_bias is not None:
            output += ("Remember, you are role-playing as a real person. You have a strong confirmation bias. "
                       "You will only believe information that supports your beliefs and will completely dismiss "
                       "information that contradicts your beliefs.\n")

        if len(chat_list) > 0:
            for chat_entry in chat_list:
                cur_person = chat_entry.entity
                current_name = "Me" if cur_person is self_person else cur_person.name
                output += f"{current_name}: {chat_entry.answer}\n"
        else:
            output += "You are the one who starts the debate.\n\n"

        output = output.strip()
        output += end_seq
        return output
