import json
import struct
import zlib
import logging
import filedate

logger = logging.getLogger(__name__)


class ArchiveRepack:

    __file_list = []

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path

        self.__read_file_list()

        self.header = open(f"{self.output_path}.hed", "wb")
        self.package = open(f"{self.output_path}.pkg", "wb")

    def __read_file_list(self):
        with open(f"{self.input_path}/file_list.json", "r") as f:
            self.__file_list = json.load(f)

    def repack(self):
        for filename, md5 in self.__file_list.items():
            logger.info(f"Packing {filename}...")

            header_length = 0x10

            self.header.write(bytes.fromhex(md5))
            filepath = f"{self.input_path}/{filename}"
            with open(f"{filepath}.json", "r") as f:
                file_config = json.load(f)

            with open(filepath, "rb") as f:
                file_data, decompressed_length = self.__pad_data(f.read())

                file_dates = filedate.File(filepath).get()
                creation_time = file_dates.get("created")

            if not file_config["encrypt"]:
                compressed_length = -2
            elif not file_config["compress"]:
                compressed_length = -1

            if file_config["compress"]:
                file_data, compressed_length = self.__pad_data(zlib.compress(file_data))

            if file_config["encrypt"]:
                logger.warning("Encrypted assets are not supported yet, skipping...")
                return

            offset = self.package.tell()

            data_size = len(file_data)
            asset_size = data_size + header_length

            self.header.write(int.to_bytes(offset, 8, "little"))
            self.header.write(int.to_bytes(asset_size, 4, "little"))
            self.header.write(int.to_bytes(data_size, 4, "little"))

            self.package.write(int.to_bytes(decompressed_length, 4, "little"))
            self.package.write(int.to_bytes(0, 4, "little"))
            self.package.write(
                int.to_bytes(compressed_length, 4, "little", signed=True)
            )

            timestamp = int(creation_time.timestamp())

            self.package.write(int.to_bytes(timestamp, 4, "little"))
            self.package.write(file_data)

    def __pad_data(self, data):
        """Pad data to 16 bytes. (If not already)"""
        orig_length = len(data)
        length = orig_length

        if length % 16 != 0:
            length += 16 - (length % 16)

        return data + b"\xCD" * (length - orig_length), orig_length
