from dataclasses import dataclass


@dataclass
class Header:
    signature: str
    version: int

    unknown_1: int
    unknown_2: int

    layout_count: int
    message_count: int

    message_offset: int
    layout_offset: int
    text_offset: int

    unknown_3: int
