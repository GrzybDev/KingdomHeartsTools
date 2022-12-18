from dataclasses import dataclass

from PIL import Image


@dataclass
class ImageData:
    totalImageLength: int
    paletteLength: int
    imageDataLength: int
    headerLength: int
    colorEntries: int
    imageFormat: int
    mipmapCount: int
    clutFormat: int
    bitsPerPixel: int
    imageWidth: int
    imageHeight: int
    gsTEX0: int
    gsTEX1: int
    gsRegs: int
    gsTexClut: int
