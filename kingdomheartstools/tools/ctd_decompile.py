import json
import sys
import unicodedata
from pathlib import Path

from polib import POEntry, POFile

from kingdomheartstools.common.ctd.LayoutBBS import LayoutBBS

from ..common.ctd.Header import Header
from ..common.ctd.LayoutReMIX import LayoutReMIX
from ..common.ctd.MessageHeader import MessageHeader
from ..common.ctd.Text import Text


class CTDDecompile:
    def __init__(self, input_path):
        self.header = None

        self.message_entries = []
        self.layout_entries = []
        self.text_entries = []

        self.last_offset = -1
        self.offset_multiplier = 0

        self.input_path = input_path
        self.ctd = open(input_path, "rb")

        self.__read_header()

    def __read_header(self):
        self.header = Header(
            signature=self.ctd.read(4).decode("utf-8"),
            version=int.from_bytes(self.ctd.read(4), "little"),
            unknown_1=int.from_bytes(self.ctd.read(2), "little"),
            unknown_2=int.from_bytes(self.ctd.read(2), "little"),
            layout_count=int.from_bytes(self.ctd.read(2), "little"),
            message_count=int.from_bytes(self.ctd.read(2), "little"),
            message_offset=int.from_bytes(self.ctd.read(4), "little"),
            layout_offset=int.from_bytes(self.ctd.read(4), "little"),
            text_offset=int.from_bytes(self.ctd.read(4), "little"),
            unknown_3=int.from_bytes(self.ctd.read(4), "little"),
        )

        if self.header.signature != "@CTD":
            raise Exception("Invalid signature")

        if self.header.message_offset != self.ctd.tell():
            raise Exception(
                "Invalid message offset (Expected "
                + str(self.header.message_offset)
                + ", got "
                + str(self.ctd.tell())
                + ")"
            )

        for i in range(self.header.message_count):
            self.message_entries.append(self.__read_message_header())

        self.ctd.seek(self.header.layout_offset)

        for i in range(self.header.layout_count):
            self.layout_entries.append(self.__read_layout())

        self.ctd.seek(self.header.text_offset)

        for i, text in enumerate(self.message_entries):
            self.ctd.seek(text.offset)

            # Read null terminated UTF-16 (version 503) or cp932 (version 1) string
            text = b""

            while True:
                if self.header.version == 503:
                    char = self.ctd.read(2)
                else:
                    char = self.ctd.read(1)

                if int.from_bytes(char, "little") == 0:
                    break

                text += char

            text = text.decode("utf-16" if self.header.version == 503 else "cp932")
            self.text_entries.append(Text(index=i, text=self.__format_string(text)))

    def __read_message_header(self):
        offset_size = 2 if self.header.version == 503 else 4

        message = MessageHeader(
            id=int.from_bytes(self.ctd.read(2), "little"),
            set=int.from_bytes(self.ctd.read(2), "little"),
            offset=int.from_bytes(self.ctd.read(offset_size), "little"),
            layoutIndex=int(
                int.from_bytes(self.ctd.read(offset_size), "little") / 0x10
            ),
        )

        if self.header.version == 503:
            message.offset = message.offset - self.header.text_offset

            real_offset = (
                self.header.text_offset
                + ((0xFFFF * self.offset_multiplier) + message.offset)
                + self.offset_multiplier
            )

            if real_offset < self.last_offset:
                self.offset_multiplier += 1
                real_offset = self.header.text_offset + (
                    (0xFFFF * self.offset_multiplier) + message.offset
                )

            message.offset = real_offset
            self.last_offset = real_offset
        return message

    def __read_layout(self):
        if self.header.version == 1:
            return LayoutBBS(
                dialogX=int.from_bytes(self.ctd.read(2), "little"),
                dialogY=int.from_bytes(self.ctd.read(2), "little"),
                dialogWidth=int.from_bytes(self.ctd.read(2), "little"),
                dialogHeight=int.from_bytes(self.ctd.read(2), "little"),
                dialogAlignment=int.from_bytes(self.ctd.read(1), "little"),
                dialogBorders=int.from_bytes(self.ctd.read(1), "little"),
                textAlignment=int.from_bytes(self.ctd.read(1), "little"),
                unknown_1=int.from_bytes(self.ctd.read(1), "little"),
                fontSize=int.from_bytes(self.ctd.read(2), "little"),
                horizontalSpace=int.from_bytes(self.ctd.read(2), "little"),
                verticalSpace=int.from_bytes(self.ctd.read(2), "little"),
                textX=int.from_bytes(self.ctd.read(2), "little"),
                textY=int.from_bytes(self.ctd.read(2), "little"),
                dialogHook=int.from_bytes(self.ctd.read(2), "little"),
                dialogHookX=int.from_bytes(self.ctd.read(2), "little"),
                unknown_2=int.from_bytes(self.ctd.read(2), "little"),
                unknown_3=int.from_bytes(self.ctd.read(2), "little"),
                unknown_4=int.from_bytes(self.ctd.read(2), "little"),
            )
        else:
            return LayoutReMIX(
                unknown_1=int.from_bytes(self.ctd.read(2), "little"),
                unknown_2=int.from_bytes(self.ctd.read(2), "little"),
                unknown_3=int.from_bytes(self.ctd.read(2), "little"),
                unknown_4=int.from_bytes(self.ctd.read(2), "little"),
                unknown_5=int.from_bytes(self.ctd.read(1), "little"),
                unknown_6=int.from_bytes(self.ctd.read(1), "little"),
                unknown_7=int.from_bytes(self.ctd.read(1), "little"),
                unknown_8=int.from_bytes(self.ctd.read(1), "little"),
                unknown_9=int.from_bytes(self.ctd.read(2), "little"),
                unknown_10=int.from_bytes(self.ctd.read(2), "little"),
                unknown_11=int.from_bytes(self.ctd.read(2), "little"),
                unknown_12=int.from_bytes(self.ctd.read(2), "little"),
            )

    def __format_string(self, text):
        priv_chars = "".join(c for c in text if unicodedata.category(c) in {"Co"})

        if len(priv_chars) > 0:
            for priv_char in priv_chars:
                text = text.replace(priv_char, "{%s}" % ord(priv_char), 1)

        return text

    def decompile(self):
        meta_file = {
            "general": {
                "version": self.header.version,
                "unknown_1": self.header.unknown_1,
                "unknown_2": self.header.unknown_2,
                "unknown_3": self.header.unknown_3,
            },
            "messages": [],
            "layouts": [],
        }

        for message in self.message_entries:
            meta_file["messages"].append(message.__dict__)

        for layout in self.layout_entries:
            meta_file["layouts"].append(layout.__dict__)

        with open(
            Path(self.input_path).with_suffix(".meta"), "w", encoding="utf-8"
        ) as output:
            json.dump(meta_file, output)

        po = POFile()

        for text in self.text_entries:
            po.append(POEntry(msgid=text.text, msgstr=""))

        po.save(Path(self.input_path).with_suffix(".po"))
