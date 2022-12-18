from dataclasses import dataclass


@dataclass
class MessageHeader:
    id: int
    set: int
    offset: int
    layoutIndex: int
