import glob
import json
import os
import re
from pathlib import Path

from PIL import Image

from kingdomheartstools.common.tim.ImageData import ImageData
from kingdomheartstools.helpers.TIM2 import TIM2


class FontGenerate:
    def __init__(self, input_folder) -> None:
        self.font_name = os.path.basename(input_folder)

        with open(Path(input_folder) / "font.json", "rb") as f:
            self.font_meta = json.load(f)

        self.image = Image.new(
            "RGBA", (self.font_meta["texture_width"], self.font_meta["texture_height"])
        )

        self.char_images = glob.glob(os.path.join(input_folder, "*.png"))
        self.char_images.sort(
            key=lambda var: [
                int(x) if x.isdigit() else x for x in re.findall(r"[^0-9]|[0-9]+", var)
            ]
        )
        self.output_path = Path(f"{input_folder}/out/")

    def __save_font_meta(self):
        with open(self.output_path / f"{self.font_name}.inf", "wb") as f:
            f.write(int.to_bytes(len(self.char_images), 2, "little"))
            f.write(int.to_bytes(self.font_meta["texture_width"], 2, "little"))
            f.write(int.to_bytes(self.font_meta["texture_height"], 2, "little"))
            f.write(int.to_bytes(self.font_meta["char_width"], 1, "little"))
            f.write(int.to_bytes(self.font_meta["char_height"], 1, "little"))

            f.write(b"\xCD" * 8)

    def generate(self):
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.__save_font_meta()

        current_x = 0
        current_y = 0

        with open(Path(self.output_path) / f"{self.font_name}.cod", "wb") as cod:
            for filename in self.char_images:
                with open(
                    Path(filename).with_suffix(".json"), "r", encoding="utf-8"
                ) as f:
                    char_meta = json.load(f)

                char_image = Image.open(filename)
                char_width, _ = char_image.size

                cod.write(char_meta["char"].encode("utf-16-le"))
                cod.write(int.to_bytes(current_x, 2, "little"))
                cod.write(int.to_bytes(current_y, 2, "little"))
                cod.write(int.to_bytes(char_meta["alpha"], 1, "little"))
                cod.write(int.to_bytes(char_width, 1, "little"))

                self.image.paste(char_image, (current_x, current_y))

                if (
                    current_x + self.font_meta["char_width"]
                    == self.font_meta["texture_width"]
                ):
                    current_x = 0
                    current_y += self.font_meta["char_height"]
                else:
                    current_x += self.font_meta["char_width"]

        tim = TIM2()
        texture_meta = self.font_meta["texture"]
        tim.version = texture_meta["version"]
        tim.image_info.append(
            ImageData(
                totalImageLength=texture_meta["totalImageLength"],
                paletteLength=texture_meta["paletteLength"],
                imageDataLength=texture_meta["imageDataLength"],
                headerLength=texture_meta["headerLength"],
                colorEntries=texture_meta["colorEntries"],
                imageFormat=texture_meta["imageFormat"],
                mipmapCount=texture_meta["mipmapCount"],
                clutFormat=texture_meta["clutFormat"],
                bitsPerPixel=texture_meta["bitsPerPixel"],
                imageWidth=texture_meta["imageWidth"],
                imageHeight=texture_meta["imageHeight"],
                gsTEX0=texture_meta["gsTEX0"],
                gsTEX1=texture_meta["gsTEX1"],
                gsRegs=texture_meta["gsRegs"],
                gsTexClut=texture_meta["gsTexClut"],
            )
        )
        tim.images.append(self.image)
        tim.save(self.output_path / f"{self.font_name}.tm2")
