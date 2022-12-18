import glob
import json
import os
from pathlib import Path

from PIL import Image

from kingdomheartstools.common.l2d.Header import Header
from kingdomheartstools.common.l2d.SQ2P import SQ2P
from kingdomheartstools.common.tim.ImageData import ImageData
from kingdomheartstools.helpers.TIM2 import TIM2


class L2DBuild:

    image_map = {}

    def __init__(self, input_folder, original_file_path):
        self.images = glob.glob(os.path.join(input_folder, "*.png"))

        for image in self.images:
            filename = Path(image).stem
            group, index = filename.split("_")

            image_group = self.image_map.get(group, {})
            image_group[index] = Image.open(image)
            self.image_map[group] = image_group

        self.input_folder = Path(input_folder)
        self.original_file_path = original_file_path

    def build(self):
        self.l2d = open(self.original_file_path, "rb+")
        self.__read_header()

        for i in range(self.header.sq2p_count):
            self.__overwrite_sq2p(str(i))

    def __read_header(self):
        signature = self.l2d.read(4).decode("utf-8")

        if signature != "L2D@":
            raise Exception("Invalid L2D signature")

        self.header = Header(
            version=self.l2d.read(4).decode("utf-8"),
            date=self.l2d.read(8).decode("utf-8"),
            name=self.l2d.read(4).decode("utf-8"),
            unknown_1=int.from_bytes(self.l2d.read(4), "little"),
            unknown_2=int.from_bytes(self.l2d.read(8), "little"),
            sq2p_count=int.from_bytes(self.l2d.read(4), "little"),
            sq2p_offset=int.from_bytes(self.l2d.read(4), "little"),
            ly2_offset=int.from_bytes(self.l2d.read(4), "little"),
            file_size=int.from_bytes(self.l2d.read(4), "little"),
            unknown_3=int.from_bytes(self.l2d.read(16), "little"),
        )

        self.l2d.seek(self.header.sq2p_offset + 16)

    def __overwrite_sq2p(self, group):
        sq2p_offset = self.l2d.tell()

        if self.l2d.read(4).decode("utf-8") != "SQ2P":
            raise Exception("Invalid SQ2P signature")

        sq2p = SQ2P(
            version=self.l2d.read(4).decode("utf-8"),
            unknown_1=int.from_bytes(self.l2d.read(8), "little"),
            sp2_offset=int.from_bytes(self.l2d.read(4), "little"),
            sq2_offset=int.from_bytes(self.l2d.read(4), "little"),
            tm2_offset=int.from_bytes(self.l2d.read(4), "little"),
            unknown_2=int.from_bytes(self.l2d.read(36), "little"),
        )

        self.l2d.seek(sq2p_offset + sq2p.tm2_offset)

        images = self.image_map[group]
        tim = TIM2()

        for index in images:
            with open(self.input_folder / f"{group}_{index}.json", "rb") as f:
                tim_meta = json.load(f)

            tim.version = tim_meta["version"]

            tim.image_info.append(
                ImageData(
                    totalImageLength=tim_meta["totalImageLength"],
                    paletteLength=tim_meta["paletteLength"],
                    imageDataLength=tim_meta["imageDataLength"],
                    headerLength=tim_meta["headerLength"],
                    colorEntries=tim_meta["colorEntries"],
                    imageFormat=tim_meta["imageFormat"],
                    mipmapCount=tim_meta["mipmapCount"],
                    clutFormat=tim_meta["clutFormat"],
                    bitsPerPixel=tim_meta["bitsPerPixel"],
                    imageWidth=tim_meta["imageWidth"],
                    imageHeight=tim_meta["imageHeight"],
                    gsTEX0=tim_meta["gsTEX0"],
                    gsTEX1=tim_meta["gsTEX1"],
                    gsRegs=tim_meta["gsRegs"],
                    gsTexClut=tim_meta["gsTexClut"],
                )
            )

            tim.images.append(images[str(index)])

        tim.save(self.l2d)
