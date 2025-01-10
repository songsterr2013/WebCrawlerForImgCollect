import json
import time
import random
import os

def to_json(links: list):
    with open("urls.json", "w") as f:
        json.dump(links, f)

def read_json(file):
    with open(file, "r") as f:
        saved_urls = json.load(f)
    return saved_urls

def url_generator(url_list: list):
    for url in url_list:
        yield url

def time_stoper(delay:int):
    time.sleep(delay + random.uniform(0, 1))

def make_folder(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def to_uppercase(input_string):
    if not isinstance(input_string, str):
        raise ValueError("str only")
    return input_string.upper()
