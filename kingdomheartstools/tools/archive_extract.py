import glob
import hashlib
import json
import logging
import os
import sys
import zlib
from datetime import datetime
from io import BytesIO
from pathlib import Path

import filedate

from kingdomheartstools.common.RemasteredEntry import RemasteredEntry
from kingdomheartstools.helpers.EGSEncryption import EGSEncryption

from ..common.AssetHeader import AssetHeader
from ..common.constants import languages, worlds
from ..common.HeaderEntry import HeaderEntry
from ..resources import path as resource_path

logger = logging.getLogger(__name__)


class ArchiveExtract:
    def __init__(self, input_path, output_path):
        self.__file_map = {}
        self.__file_list = {}

        self.package = open(Path(input_path).with_suffix(".pkg"), "rb")
        self.output_path = output_path

        self.__load_file_map()
        self.__read_header(Path(input_path).with_suffix(".hed"))

    def __load_file_map(self):
        for language in languages:
            for world in worlds:
                for index in range(64):
                    ard_filename = os.path.join(
                        "ard/", language, f"{world}{index:02d}.ard"
                    ).replace("\\", "/")
                    map_filename = os.path.join(
                        "map", language, f"{world}{index:02d}.map"
                    ).replace("\\", "/")
                    bar_filename = os.path.join(
                        "map", language, f"{world}{index:02d}.bar"
                    ).replace("\\", "/")

                    self.__file_map[
                        hashlib.md5(ard_filename.encode()).hexdigest()
                    ] = ard_filename
                    self.__file_map[
                        hashlib.md5(map_filename.encode()).hexdigest()
                    ] = map_filename
                    self.__file_map[
                        hashlib.md5(bar_filename.encode()).hexdigest()
                    ] = bar_filename

        for additional_file in [
            "item-011.imd",
            "KH2.IDX",
            "ICON/ICON0.PNG",
            "ICON/ICON0_EN.png",
        ]:
            md5 = hashlib.md5(additional_file.encode()).hexdigest()
            self.__file_map[md5] = additional_file.strip()

        for file in glob.glob(f"{resource_path}/*.txt"):
            with open(file, "r", encoding="utf-8") as f:
                file_list = f.readlines()

                for file_name in file_list:
                    additional_files = []
                    filename = file_name.strip()

                    if filename.find("anm/") != -1:
                        additional_files.append(filename.replace("anm/", "anm/jp/"))
                        additional_files.append(filename.replace("anm/", "anm/us/"))
                        additional_files.append(filename.replace("anm/", "anm/fm/"))

                    if filename.find("bgm/") != -1:
                        additional_files.append(filename.replace(".bgm", ".win32.scd"))

                    if filename.find("se/") != -1:
                        additional_files.append(filename.replace(".seb", ".win32.scd"))

                    if filename.find("vagstream/") != -1:
                        additional_files.append(filename.replace(".vas", ".win32.scd"))

                    if filename.find("gumibattle/se/") != -1:
                        additional_files.append(filename.replace(".seb", ".win32.scd"))

                    if filename.find("voice/") != -1:
                        additional_files.append(filename.replace(".vag", ".win32.scd"))
                        additional_files.append(filename.replace(".vsb", ".win32.scd"))

                    md5 = hashlib.md5(filename.encode()).hexdigest()
                    self.__file_map[md5] = filename

                    for additional_file in additional_files:
                        md5 = hashlib.md5(additional_file.encode()).hexdigest()
                        self.__file_map[md5] = additional_file

    def __read_header(self, header_path):
        header_length = os.stat(header_path).st_size
        entries_count = int(header_length / 0x20)

        file_list_out = {}

        with open(header_path, "rb") as header:
            for _ in range(entries_count):
                md5 = header.read(0x10).hex()
                filename = self.__file_map.get(md5, f"{md5}.raw")

                entry = HeaderEntry(
                    md5=md5,
                    offset=int.from_bytes(header.read(0x8), "little"),
                    dataLength=int.from_bytes(header.read(0x4), "little"),
                    actualLength=int.from_bytes(header.read(0x4), "little"),
                )

                self.__file_list[filename] = entry
                file_list_out[filename] = entry.md5

            if header_length != header.tell():
                logger.error(
                    "Header length does not match, something is wrong with the archive, exiting..."
                )
                sys.exit(1)

            Path(self.output_path).mkdir(parents=True, exist_ok=True)

            with open(f"{self.output_path}/file_list.json", "w", encoding="utf-8") as f:
                json.dump(file_list_out, f)

    def extract(self):
        for filename, entry in self.__file_list.items():
            # Create the output directory if it doesn't exist
            output_dir = Path(self.output_path) / Path(filename).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Extracting {filename}...")
            output_path = Path(self.output_path) / filename

            self.__extract_asset(output_path, entry)

    def __extract_asset(self, filepath, entry):
        self.package.seek(entry.offset)

        header_raw_bytes = self.package.read(0x10)
        header_raw = BytesIO(header_raw_bytes)

        encryption_key = EGSEncryption.generate_key(header_raw_bytes)

        asset_header = AssetHeader(
            decompressedLength=int.from_bytes(header_raw.read(0x4), "little"),
            remasteredAssetCount=int.from_bytes(header_raw.read(0x4), "little"),
            compressedLength=int.from_bytes(
                header_raw.read(0x4), "little", signed=True
            ),
            creationDate=datetime.fromtimestamp(
                int.from_bytes(header_raw.read(0x4), "little")
            ),
        )

        remastered_assets_headers = []

        for i in range(asset_header.remasteredAssetCount):
            remastered_assets_headers.append(
                RemasteredEntry(
                    name=self.package.read(0x20).decode("utf-8").strip("\0"),
                    offset=int.from_bytes(self.package.read(4), "little"),
                    originalAssetOffset=int.from_bytes(self.package.read(4), "little"),
                    decompressedLength=int.from_bytes(self.package.read(4), "little"),
                    compressedLength=int.from_bytes(
                        self.package.read(4), "little", signed=True
                    ),
                )
            )

        with open(filepath, "wb") as writer:
            filedate.File(filepath).set(created=asset_header.creationDate)
            writer.write(self.__get_asset_data(asset_header, encryption_key))

            with open(f"{filepath}.json", "w", encoding="utf-8") as f:
                file_config = {
                    "encrypt": asset_header.compressedLength > -2,
                    "compress": asset_header.compressedLength > -1,
                }

                json.dump(file_config, f)

        remastered_folder = os.path.join(
            os.path.dirname(filepath), "remastered_" + os.path.basename(filepath)
        )
        remastered_folder = Path(remastered_folder)

        for remastered_asset_header in remastered_assets_headers:
            logger.info(
                f"Extracting remastered asset {remastered_asset_header.name}..."
            )

            if self.package.tell() % 0x10 != 0:
                self.package.seek(0x10 - (self.package.tell() % 0x10), 1)

            Path(remastered_folder / remastered_asset_header.name).parent.mkdir(
                parents=True, exist_ok=True
            )
            with open(remastered_folder / remastered_asset_header.name, "wb") as writer:
                writer.write(
                    self.__get_asset_data(remastered_asset_header, encryption_key)
                )

    def __get_asset_data(self, header, encryption_key):
        data_length = (
            header.compressedLength
            if header.compressedLength >= 0
            else header.decompressedLength
        )

        packet_data = self.package.read(data_length)

        if header.compressedLength > -2:
            for i in range(0, min(len(packet_data), 0x100), 0x10):
                packet_data = EGSEncryption.decrypt_chunk(
                    encryption_key, packet_data, i
                )

        if header.compressedLength > -1:
            return self.__decompress_asset_data(packet_data, header.decompressedLength)
        else:
            return packet_data

    def __decompress_asset_data(self, data, expected_length):
        decompressed_data = zlib.decompress(data)

        if len(decompressed_data) != expected_length:
            logger.warning(
                "Decompressed data length does not match, something is wrong with the archive... (expected: %d, got: %d)"
                % (expected_length, len(decompressed_data))
            )

        return decompressed_data
