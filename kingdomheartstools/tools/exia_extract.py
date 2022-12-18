import xml.etree.ElementTree as ET
from pathlib import Path

from polib import POEntry, POFile


class ExiaExtract:
    def __init__(self, input_path) -> None:
        with open(input_path, "r", encoding="cp932") as f:
            data = f.read().strip("ﾍ")

        self.tree = ET.ElementTree(ET.fromstring(data))
        self.output_path = Path(input_path).with_suffix(".po")

    def extract(self: bool):
        po = POFile()

        root = self.tree.getroot()
        schedule = root.find("SCHEDULE")

        schedule_categories = schedule.findall("SCHEDULE_CATEGORY")

        for category in schedule_categories:
            if category.attrib["type"] == "SCHEDULE_CATEGORY_TEXT_MOVIE":
                params = category.findall("PARAM")

                correct_lang = False
                for param in params:
                    if param.attrib["Language"] == "LANGUAGE_EN":
                        correct_lang = True
                        break

                if not correct_lang:
                    continue

                schedule_text_movie = category.find("SCHEDULE_TEXT_MOVIE")
                text_movie = schedule_text_movie.find("TEXT_MOVIE")

                for text in text_movie:
                    po.append(POEntry(msgid=text.attrib["Text"], msgstr=""))

        po.save(self.output_path)
