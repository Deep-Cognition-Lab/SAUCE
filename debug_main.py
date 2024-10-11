import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"


def main():

    # load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    # get input
    input_text = "Hi, do you know the rules of the party game Mafia?"  # input("insert input for the model: ")

    # generate
    inputs = tokenizer(input_text, return_tensors="pt")
    inputs = {'input_ids': inputs.input_ids[0, :],
              'attention_mask': inputs.attention_mask[0, :]}
    inputs = {'input_ids': torch.unsqueeze(inputs['input_ids'], 0),
              'attention_mask': torch.unsqueeze(inputs['attention_mask'], 0)}
    inputs = {key: value.to(device) for key, value in inputs.items()}
    with torch.inference_mode():
        outputs = model.generate(**inputs,
                                 # max_length=self.max_source_length,
                                 # num_beams=self.num_beams
                                 # max_new_tokens=100
                                 )
    print(tokenizer.decode(outputs[0]
                           # , skip_special_tokens=self.generate_without_special_tokens
                           ))


if __name__ == '__main__':
    main()
