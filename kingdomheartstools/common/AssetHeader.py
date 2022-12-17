from dataclasses import dataclass
from datetime import datetime


@dataclass
class AssetHeader:
    decompressedLength: int
    remasteredAssetCount: int
    compressedLength: int
    creationDate: datetime
