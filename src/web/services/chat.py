import os

import requests

from models.chat_get_image import ChatGetImageInput
from models.chat_get_image_contents import ChatGetImageContents
from models.chat_get_thread import ChatGetThreadInput
from models.chat_input import ChatInput

api_base_url = os.getenv("services__api__api__0", "")


def create_thread():
    result = requests.post(url=f"{api_base_url}/v1/create_thread",
                           timeout=30)
    if result.ok:
        return result.json()['thread_id']

    return None


def chat(thread_id,
         content):

    chat_input = ChatInput(thread_id=thread_id,
                           content=content)

    response = requests.post(url=f"{api_base_url}/v1/chat",
                             json=chat_input.model_dump(mode="json"),
                             stream=True,
                             timeout=300
                             )

    buffer = ""
    for chunk in response.iter_content(chunk_size=None):
        if not chunk:
            continue
        buffer += chunk.decode('utf-8')
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if line.strip():
                yield line  # Each line is a complete JSON object


def get_thread(thread_id):
    get_thread_input = ChatGetThreadInput(thread_id=thread_id)

    response = requests.get(url=f"{api_base_url}/v1/get_thread",
                            data=get_thread_input.model_dump(mode="python"),
                            timeout=60)

    return response.json()


def get_image(file_id):
    get_image_input = ChatGetImageInput(file_id=file_id)

    image = requests.get(
        url=f"{api_base_url}/v1/get_image",
        json=get_image_input.model_dump(mode="json"),
        timeout=60
    )

    return image.content


def get_image_contents(thread_id):
    get_image_input = ChatGetImageContents(thread_id=thread_id)

    image_contents = requests.get(
        url=f"{api_base_url}/v1/get_image_contents",
        json=get_image_input.model_dump(mode="json"),
        timeout=60
    )

    return image_contents.json()


__all__ = ["chat", "get_image", "get_thread", "get_image_contents", "create_thread",]
