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

from ..common.AssetHeader import AssetHeader
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
        for file in glob.glob(f"{resource_path}/*.txt"):
            with open(file, "r", encoding="utf-8") as f:
                file_list = f.readlines()

                for file_name in file_list:
                    md5 = hashlib.md5(file_name.encode().strip()).hexdigest()
                    self.__file_map[md5] = file_name.strip()

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

        header_raw = BytesIO(self.package.read(0x10))

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

        if asset_header.remasteredAssetCount > 0:
            logger.warning(
                "Assets that are remastered are not supported yet, skipping..."
            )
            return

        with open(filepath, "wb") as writer:
            filedate.File(filepath).set(created=asset_header.creationDate)
            writer.write(self.__get_asset_data(asset_header))

            with open(f"{filepath}.json", "w", encoding="utf-8") as f:
                file_config = {
                    "encrypt": asset_header.compressedLength > -2,
                    "compress": asset_header.compressedLength > -1,
                }

                json.dump(file_config, f)

    def __get_asset_data(self, header):
        data_length = (
            header.compressedLength
            if header.compressedLength >= 0
            else header.decompressedLength
        )

        packet_data = self.package.read(data_length)

        if header.compressedLength > -2:
            logger.warning("Encrypted assets are not supported yet, skipping...")
            return

        if header.compressedLength > -1:
            return self.__decompress_asset_data(packet_data, header.decompressedLength)
        else:
            return packet_data

    def __decompress_asset_data(self, data, expected_length):
        decompressed_data = zlib.decompress(data)

        if len(decompressed_data) != expected_length:
            logger.error(
                "Decompressed data length does not match, something is wrong with the archive, exiting..."
            )
            sys.exit(1)

        return decompressed_data
