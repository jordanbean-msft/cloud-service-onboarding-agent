import json

# import pandas as pd
# import matplotlib.pyplot as plt


def output_formatter(content):
    try:
        content = json.loads(content)

        if content['content_type'] == "markdown":
            return content['content']

        if content['content_type'] == "image":
            return content['content']

        return content['content']

    except:
        # if the content isn't json, return it as is
        pass

    return content

def replace_annotation_placeholder(original, start, end, replacement):
    if not (0 <= start <= end <= len(original)):
        raise ValueError("Invalid start or end index")
    return f"{original[:start]}({replacement}){original[end:]}"

__all__ = ["output_formatter", "replace_annotation_placeholder"]
