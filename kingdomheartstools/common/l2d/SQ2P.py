from dataclasses import dataclass


@dataclass
class SQ2P:
    version: str
    unknown_1: int

    sp2_offset: int
    sq2_offset: int
    tm2_offset: int

    unknown_2: int
