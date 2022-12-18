import json
import re
from pathlib import Path

from polib import pofile


class CTDCompile:
    def __init__(self, input_path):
        metadata_path = Path(input_path).with_suffix(".meta")

        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)

        po_path = Path(input_path).with_suffix(".po")
        self.po = pofile(pofile=po_path)

        self.output_path = Path(input_path).with_suffix(".ctd")

    def compile(self):
        with open(self.output_path, "wb") as f:
            message_block_offset = 0x20
            layout_block_offset = message_block_offset + (
                len(self.metadata["messages"]) * 8
            )

            layout_block_offset += (
                0
                if layout_block_offset % 0x10 == 0
                else 0x10 - (layout_block_offset % 0x10)
            )

            text_block_offset = layout_block_offset + (
                len(self.metadata["layouts"]) * 20
            )

            f.write(b"@CTD")
            f.write(int.to_bytes(self.metadata["general"]["version"], 4, "little"))
            f.write(int.to_bytes(self.metadata["general"]["unknown_1"], 2, "little"))
            f.write(int.to_bytes(self.metadata["general"]["unknown_2"], 2, "little"))
            f.write(int.to_bytes(len(self.metadata["layouts"]), 2, "little"))
            f.write(int.to_bytes(len(self.metadata["messages"]), 2, "little"))
            # Message block offset
            f.write(int.to_bytes(message_block_offset, 4, "little"))
            # Layout block offset
            f.write(int.to_bytes(layout_block_offset, 4, "little"))
            # Text block offset
            f.write(
                int.to_bytes(
                    text_block_offset,
                    4,
                    "little",
                )
            )
            f.write(int.to_bytes(self.metadata["general"]["unknown_3"], 4, "little"))

            # Do placeholder for message block
            message_block_length = len(self.metadata["messages"]) * 8
            placeholder_length = (
                message_block_length
                if message_block_length % 0x10 == 0
                else (message_block_length + (0x10 - (message_block_length % 0x10)))
            )

            f.write(b"\x00" * placeholder_length)

            for layout in self.metadata["layouts"]:
                self.__write_layout(f, layout)

            for i, text in enumerate(self.po):
                start_offset = self.__write_text(f, text)
                end_offset = f.tell()

                f.seek(0x20 + (i * 8))  # Seek to message block

                message = self.metadata["messages"][i]

                f.write(int.to_bytes(message["id"], 2, "little"))
                f.write(int.to_bytes(message["set"], 2, "little"))
                f.write(int.to_bytes(start_offset, 2, "little"))
                f.write(int.to_bytes(message["layoutIndex"] * 0x10, 2, "little"))

                f.seek(end_offset)

            f.write(b"\xCD" * (0 if f.tell() % 0x10 == 0 else 0x10 - (f.tell() % 0x10)))

    def __write_layout(self, writer, layout):
        writer.write(int.to_bytes(layout["unknown_1"], 2, "little"))
        writer.write(int.to_bytes(layout["unknown_2"], 2, "little"))
        writer.write(int.to_bytes(layout["unknown_3"], 2, "little"))
        writer.write(int.to_bytes(layout["unknown_4"], 2, "little"))
        writer.write(int.to_bytes(layout["unknown_5"], 1, "little"))
        writer.write(int.to_bytes(layout["unknown_6"], 1, "little"))
        writer.write(int.to_bytes(layout["unknown_7"], 1, "little"))
        writer.write(int.to_bytes(layout["unknown_8"], 1, "little"))
        writer.write(int.to_bytes(layout["unknown_9"], 2, "little"))
        writer.write(int.to_bytes(layout["unknown_10"], 2, "little"))
        writer.write(int.to_bytes(layout["unknown_11"], 2, "little"))
        writer.write(int.to_bytes(layout["unknown_12"], 2, "little"))

    def __write_text(self, writer, text):
        start_offset = writer.tell()
        text = self.__reformat_string(text.msgstr if text.msgstr != "" else text.msgid)
        writer.write(text.encode("utf-16-le"))
        return start_offset

    def __reformat_string(self, text):
        special_chars = re.findall(r"{(\d+)}", text)

        for char in special_chars:
            text = text.replace("{%s}" % char, chr(int(char)))

        return text + "\0"
