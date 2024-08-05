from __future__ import annotations
import os
import json
import torch
from transformers import AutoConfig, AutoModelForSeq2SeqLM, AutoTokenizer, AutoModelForCausalLM
from typing import List, Callable
import logging

log = logging.getLogger(__name__)


class HuggingFaceModel:
    """
    A container for a trained model, either pretrained or locally fine-tuned.
    Used for generating of output by a Person instance.
    """

    def __init__(self, local_model_path: str = None, pretrained_model_name: str = None,
                 special_tokens: List[str] = None, smart_truncation_func: Callable = None,
                 max_source_length: int = 1024, num_beams: int = 4,
                 generate_without_special_tokens: bool = False):
        if local_model_path:
            config = AutoConfig.from_pretrained(local_model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(local_model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(local_model_path, config=config)
            with open(os.path.join(local_model_path, 'config.json'), 'r') as f:
                train_config = json.load(f)
                self.model_name = train_config['_name_or_path']
            if special_tokens:
                log.warning("special_tokens argument will not be used, since a local model is used,"
                            " trained over special tokens of its own.")
            with open(os.path.join(local_model_path, 'special_tokens_map.json'), 'r') as f:
                added_tokens = json.load(f)['additional_special_tokens']
                self.special_token_ids = self._get_special_tokens_id(added_tokens)
        elif pretrained_model_name:
            self.model_name = pretrained_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name)
            if special_tokens:
                self.tokenizer.add_special_tokens({'additional_special_tokens': special_tokens})
                self.special_token_ids = self._get_special_tokens_id(special_tokens)
            else:
                self.special_token_ids = []
            # self.model = AutoModelForSeq2SeqLM.from_pretrained(pretrained_model_name)
            self.model = AutoModelForCausalLM.from_pretrained(pretrained_model_name,
                                                              torch_dtype=torch.bfloat16)
        else:
            raise ValueError("Missing either model_path or pretrained_model_name")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        self.smart_truncation_func = smart_truncation_func
        self.max_source_length = max_source_length
        self.num_beams = num_beams
        self.generate_without_special_tokens = generate_without_special_tokens

    def _get_special_tokens_id(self, added_tokens: List[str]) -> List[int]:
        return [x for x in self.tokenizer(' '.join(added_tokens)).input_ids
                if self.tokenizer.decode(x) in added_tokens]

    def generate(self, input_text: str) -> str:
        inputs = self.tokenizer(input_text, return_tensors="pt")
        inputs = {'input_ids': inputs.input_ids[0, :],
                  'attention_mask': inputs.attention_mask[0, :]}
        # TODO move inputs to dataset to use moving it to the right device, example:
        # from datasets import Dataset
        # my_dict = {"a": [1, 2, 3]}
        # dataset = Dataset.from_dict(my_dict)
        if self.smart_truncation_func:
            inputs = self.smart_truncation_func(inputs, self.max_source_length,
                                                self.special_token_ids, self.model_name)
        inputs = {'input_ids': torch.unsqueeze(inputs['input_ids'], 0),
                  'attention_mask': torch.unsqueeze(inputs['attention_mask'], 0)}
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.inference_mode():
            outputs = self.model.generate(**inputs,
                                          # max_length=self.max_source_length,
                                          # num_beams=self.num_beams
                                          max_new_tokens=100
                                          )
        return self.tokenizer.decode(outputs[0],
                                     skip_special_tokens=self.generate_without_special_tokens)
