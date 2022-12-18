import json
import os
import struct
from pathlib import Path

from kingdomheartstools.common.l2d.Header import Header
from kingdomheartstools.common.l2d.SQ2P import SQ2P
from kingdomheartstools.helpers.TIM2 import TIM2


class L2DConvert:

    images = []

    def __init__(self, input_path) -> None:
        self.output_path = Path(input_path).parent / Path(input_path).stem
        self.l2d = open(input_path, "rb")

        self.__read_header()

        for i in range(self.header.sq2p_count):
            self.__read_sq2p()

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

    def __read_sq2p(self):
        sq2p_offset = self.l2d.tell()
        self.output_path.mkdir(parents=True, exist_ok=True)

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
        self.images.append(TIM2(reader=self.l2d))

    def convert(self):
        for group, image in enumerate(self.images):
            for idx in range(image.numImages):
                meta = image.get_image_data(idx)

                with open(
                    self.output_path / f"{group}_{idx}.json", "w", encoding="utf-8"
                ) as f:
                    json.dump(meta, f)

                image.get_image(idx).save(self.output_path / f"{group}_{idx}.png")
