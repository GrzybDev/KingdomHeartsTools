from dataclasses import dataclass


@dataclass
class Header:
    version: str
    date: str
    name: str

    unknown_1: int
    unknown_2: int

    sq2p_count: int
    sq2p_offset: int
    ly2_offset: int

    file_size: int

    unknown_3: int
