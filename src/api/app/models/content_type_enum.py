from enum import StrEnum, auto


class ContentTypeEnum(StrEnum):
    MARKDOWN = auto()
    # DATAFRAME = auto()
    # EXCEPTION = auto()
    # MATPLOTLIB = auto()
    # IMAGE = auto()
    ANNOTATION_URL = auto()
    ANNOTATION_FILE = auto()
    FILE = auto()
    SENTINEL = auto()  # Used to indicate the end of a stream


__all__ = ["ContentTypeEnum"]
