import os
import json
import openai
import os
from dotenv import load_dotenv
import sys
from transformers import GPT2Tokenizer
import mistletoe
from mistletoe.ast_renderer import ASTRenderer
from bs4 import BeautifulSoup

from consts import CHAPTERS, ESTIMATED_QUESTION_SIZE, TOP_LEVEL_COMPONENTS, MAX_CONTEXT_SIZE

load_dotenv()
openai.api_key = os.getenv("OPENAI_SECRET_KEY")
BOOK_DIR = os.path.join(os.getenv("RUST_BOOK_PATH"), "src")

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
DATA_DIR = os.path.join(PROMPTS_DIR, "data")

PROMPT_FILE = os.path.join(DATA_DIR, "prompts.json")
GENERATED_DIR = os.path.join(PROMPTS_DIR, "generated")


def get_prompts():
    with open(PROMPT_FILE) as f:
        return json.load(f)


# clean tags from html within markdown, returning only text
def clean_html(text):
    return BeautifulSoup(text, "lxml").text


# load file content from included listings
def resolve_include(text):
    # get filename after "{{#<include type>" and remove trailing "}}"
    filename = text.split(" ")

    if "include" not in filename[0]:
        return ""

    # remove anchor on path
    split_filename = filename[1].split(":")
    if len(split_filename) > 1:
        listing_path = split_filename[0]
    else:
        listing_path = filename[1][:-3]

    listing_path = os.path.join(BOOK_DIR, listing_path)

    with open(listing_path) as f:
        return f.read()


# recurse over MD AST, extracting raw text from inline elements
def find_component_text(component):
    text = []

    for child in component["children"]:
        if child["type"] == "RawText":
            # check if content includes file reference
            if child["content"].startswith("{{#"):
                text.append(resolve_include(child["content"]))
            else:
                text.append(child["content"])

        elif child["type"] == "LineBreak":
            text.append(" ")

        elif "children" in child:
            text.append(find_component_text(child))

    if component["type"] in TOP_LEVEL_COMPONENTS:
        text.append("\n")

    return clean_html("".join(text))


# whether a top-level markdown child is valid for parsing
def component_is_valid(component):
    return component["type"] in TOP_LEVEL_COMPONENTS


def extract_component_info(component):
    text = find_component_text(component)
    tokens = tokenizer(text)["input_ids"]

    return {
        "text": text,
        "tokens": len(tokens),
    }


def parse_chapter(chapter):
    chapter_file = os.path.join(BOOK_DIR, chapter)

    if not os.path.exists(chapter_file):
        raise ValueError(f"Chapter MD file {chapter} does not exist")

    with open(chapter_file) as cf:
        md = cf.read()

    # extract text and token count from parsed markdown
    parsed = json.loads(mistletoe.markdown(md, ASTRenderer))
    valid_children = filter(component_is_valid, parsed["children"])
    children_info = list(map(extract_component_info, valid_children))

    return children_info


def shard_chapter(chapter_components):
    shards = []
    num_tokens = 0
    curr_prompt = ""

    for component in chapter_components:
        component_tokens = component["tokens"]
        component_text = component["text"]

        if num_tokens + component_tokens > MAX_CONTEXT_SIZE:
            shards.append(curr_prompt)

            curr_prompt = component_text
            num_tokens = component_tokens
        else:
            curr_prompt += component_text
            num_tokens += component_tokens

    shards.append(curr_prompt)
    return shards


# create directory for question generation iteration
def create_output_dir():
    generation_dirs = os.listdir(GENERATED_DIR)
    last_generation = max(map(int, generation_dirs))
    next_generation = str(last_generation + 1).zfill(3)

    pass_dir = os.path.join(GENERATED_DIR, next_generation)
    prompt_dir = os.path.join(pass_dir, "prompts")
    question_dir = os.path.join(pass_dir, "questions")

    os.makedirs(prompt_dir, exist_ok=True)
    os.makedirs(question_dir, exist_ok=True)

    return prompt_dir, question_dir


def generate_prompts(files=[]):
    prompt_dir, question_dir = create_output_dir()
    prompts = get_prompts()

    for prompt_type, prompt_data in prompts.items():
        for chapter in CHAPTERS:
            chapter_components = parse_chapter(chapter)
            chapter_shards = shard_chapter(chapter_components)

            for index, shard in enumerate(chapter_shards):
                file_name = f"{chapter[:-5]}-{prompt_type}-{index}.txt"
                print(f"Running completion for prompt {index} of {file_name}")

                prompt_list = [prompt_data["before-text"],
                               shard, prompt_data["after-text"]]

                prompt = "\n".join(prompt_list)

                with open(os.path.join(prompt_dir, file_name), "w+") as f:
                    f.write(prompt)

                try:
                    completion = openai.Completion.create(
                        engine="text-davinci-002", prompt=prompt, max_tokens=5 * ESTIMATED_QUESTION_SIZE)
                except openai.error.InvalidRequestError:
                    print(
                        f"ERROR: too many tokens in prompt for {chapter}, consider splitting it into more prompts")
                    return

                print(f"Finished completion for prompt {index} of {file_name}, writing output to file")
                with open(os.path.join(question_dir, file_name), "w+") as f:
                    f.write(completion["choices"][0]["text"])


if __name__ == "__main__":
    args = sys.argv[1:]
    generate_prompts(files=args)
