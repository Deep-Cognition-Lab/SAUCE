import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"


def preprocess_input(system_info, user_instruction):
    """
    <|begin_of_text|><|start_header_id|>system<|end_header_id|>

Cutting Knowledge Date: December 2023
Today Date: 23 July 2024

You are a helpful assistant<|eot_id|><|start_header_id|>user<|end_header_id|>

What is the capital of France?<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """
    ""
    return f"<|begin_of_text|>" \
           f"<|start_header_id|>system<|end_header_id|>{system_info}<|eot_id|>" \
           f"<|start_header_id|>user<|end_header_id|>{user_instruction}<|eot_id|>" \
           f"<|start_header_id|>assistant<|end_header_id|>"


def postprocess_output(decoded_output):
    assistant_prefix = "<|start_header_id|>assistant<|end_header_id|>"
    if assistant_prefix in decoded_output:
        decoded_output = decoded_output.split(assistant_prefix)[1]
    return decoded_output.split("<|eot_id|>")[0]


def main():

    print("Debug print: started main")

    # load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    print("Debug print: loaded tokenizer")
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    print("Debug print: loaded model")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Debug print: found device -", device)
    model.to(device)
    print("Debug print: moved model to device", device)
    model.eval()
    print("Debug print: moved model to eval mode")

    # get input
    input_text = "The game has just started and no one has posted anything yet to the group chat. " \
                 "Add the first message to the game's chat"  # input("insert input for the model: ")
    print("Debug print: got input_text -", input_text)

    # preprocess input
    system_info = "You are a player in an online game of Mafia"
    print("Debug print: got system_info -", system_info)
    prompt = preprocess_input(system_info, input_text)
    print("Debug print: preprocessed prompt -", prompt)

    # generate
    inputs = tokenizer(prompt, return_tensors="pt")
    print("Debug print: passed input through tokenizer")
    inputs = {key: value.to(device) for key, value in inputs.items()}
    print("Debug print: moved all input parts to device", device)
    with torch.inference_mode():
        print("Debug print: using torch.inference_mode()")
        outputs = model.generate(**inputs,
                                 # max_length=max_source_length,
                                 # num_beams=num_beams
                                 max_new_tokens=100
                                 )
    print("Debug print: output generated")
    decoded_output = tokenizer.decode(outputs[0]
                                      # , skip_special_tokens=self.generate_without_special_tokens
                                      )
    print("Debug print: output decoded")
    print("Decoded output:", decoded_output)



if __name__ == '__main__':
    main()
