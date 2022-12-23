from dataclasses import dataclass


@dataclass
class RemasteredEntry:
    name: str
    offset: int
    originalAssetOffset: int
    decompressedLength: int
    compressedLength: int
