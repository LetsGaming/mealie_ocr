from enum import Enum


class Models(Enum):
    """Enum for different models."""
    GPT4 = "gpt-4-turbo"
    GPT4_O = "gpt-4o"
    GPT3_5 = "gpt-3.5-turbo-0125"
    GPT3_5_TURBO = "gpt-3.5-turbo"
    GPT3_5_TURBO_0301 = "gpt-3.5-turbo-0301"
    CODE_DAVINCI_EDIT = "code-davinci-edit-001"
    TEXT_DAVINCI_EDIT = "text-davinci-edit-001"
    DAVINCI = "davinci"
    CURIE = "curie"
    BABBAGE = "babbage"
    ADA = "ada"
    DALL_E = "dall-e"
    WHISPER = "whisper-1"