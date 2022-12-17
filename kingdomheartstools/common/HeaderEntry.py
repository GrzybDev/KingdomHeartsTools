from dataclasses import dataclass
import json


@dataclass
class HeaderEntry:
    md5: str
    offset: int
    dataLength: int
    actualLength: int
