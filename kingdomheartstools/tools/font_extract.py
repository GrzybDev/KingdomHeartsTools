import json
from pathlib import Path

from kingdomheartstools.helpers.TIM2 import TIM2


class FontExtract:
    def __init__(self, input_path) -> None:
        self.__char_map = []

        font_info_path = Path(input_path).with_suffix(".inf")
        self.__read_font_info(font_info_path)

        char_map_path = Path(input_path).with_suffix(".cod")
        self.__read_char_map(char_map_path)

        self.texture_path = Path(input_path).with_suffix(".tm2")
        self.output_path = Path(input_path).with_suffix("")

    def __read_font_info(self, path):
        with open(path, "rb") as f:
            self.char_count = int.from_bytes(f.read(2), "little")
            self.texture_width = int.from_bytes(f.read(2), "little")
            self.texture_height = int.from_bytes(f.read(2), "little")
            self.char_width = int.from_bytes(f.read(1), "little")
            self.char_height = int.from_bytes(f.read(1), "little")

    def __read_char_map(self, path):
        with open(path, "rb") as f:
            for i in range(self.char_count):
                self.__char_map.append(
                    {
                        "char": f.read(2).decode("utf-16"),
                        "x_offset": int.from_bytes(f.read(2), "little"),
                        "y_offset": int.from_bytes(f.read(2), "little"),
                        "alpha": int.from_bytes(f.read(1), "little"),
                        "char_width": int.from_bytes(f.read(1), "little"),
                    }
                )

    def extract(self):
        self.output_path.mkdir(parents=True, exist_ok=True)

        font_texture = TIM2(path=self.texture_path)

        font_meta = {
            "texture_width": self.texture_width,
            "texture_height": self.texture_height,
            "char_width": self.char_width,
            "char_height": self.char_height,
            "texture": font_texture.get_image_data(),
        }

        with open(self.output_path / "font.json", "w", encoding="utf-8") as f:
            json.dump(font_meta, f)

        font = font_texture.get_image()

        for i, char in enumerate(self.__char_map):
            char_image = font.crop(
                (
                    char["x_offset"],
                    char["y_offset"],
                    char["x_offset"] + char["char_width"],
                    char["y_offset"] + self.char_height,
                )
            )

            char_image.save(self.output_path / f"{i}.png")

            with open(self.output_path / f"{i}.json", "w", encoding="utf-8") as f:
                json.dump({"char": char["char"], "alpha": char["alpha"]}, f)
