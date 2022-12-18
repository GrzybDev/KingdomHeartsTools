from pathlib import Path

from PIL import Image

from ..common.tim.ImageData import ImageData


class TIM2:
    def __init__(self, **kwargs) -> None:
        self.image_info = []
        self.images = []

        if kwargs.get("path") or kwargs.get("reader"):
            if kwargs.get("reader"):
                self.tim2 = kwargs.get("reader")
            else:
                self.tim2 = open(kwargs["path"], "rb")

            self.__read_header()

            for i in range(self.numImages):
                self.__read_image()

    def __read_header(self):
        signature = self.tim2.read(4).decode("utf-8")

        if signature != "TIM2":
            raise Exception("Invalid signature")

        self.version = int.from_bytes(self.tim2.read(2), "little")
        self.numImages = int.from_bytes(self.tim2.read(2), "little")

        self.tim2.seek(self.tim2.tell() + (self.tim2.tell() % 16))

    def __get_image_format(self, bpp):
        match bpp:
            case 2:
                return "RGB"
            case 3:
                return "RGBA"

        raise Exception("Bits per pixel not supported: " + str(bpp))

    def __read_image(self):
        start_offset = self.tim2.tell()

        image_data = ImageData(
            totalImageLength=int.from_bytes(self.tim2.read(4), "little"),
            paletteLength=int.from_bytes(self.tim2.read(4), "little"),
            imageDataLength=int.from_bytes(self.tim2.read(4), "little"),
            headerLength=int.from_bytes(self.tim2.read(2), "little"),
            colorEntries=int.from_bytes(self.tim2.read(2), "little"),
            imageFormat=int.from_bytes(self.tim2.read(1), "little"),
            mipmapCount=int.from_bytes(self.tim2.read(1), "little"),
            clutFormat=int.from_bytes(self.tim2.read(1), "little"),
            bitsPerPixel=int.from_bytes(self.tim2.read(1), "little"),
            imageWidth=int.from_bytes(self.tim2.read(2), "little"),
            imageHeight=int.from_bytes(self.tim2.read(2), "little"),
            gsTEX0=int.from_bytes(self.tim2.read(8), "little"),
            gsTEX1=int.from_bytes(self.tim2.read(8), "little"),
            gsRegs=int.from_bytes(self.tim2.read(8), "little"),
            gsTexClut=int.from_bytes(self.tim2.read(8), "little"),
        )

        self.tim2.seek(start_offset + image_data.headerLength)
        raw_image_bytes = self.tim2.read(image_data.imageDataLength)

        self.images.append(
            Image.frombytes(
                self.__get_image_format(image_data.bitsPerPixel),
                (image_data.imageWidth, image_data.imageHeight),
                raw_image_bytes,
                "raw",
            )
        )

        self.image_info.append(image_data)

    def get_image(self, index=0):
        return self.images[index]

    def get_image_data(self, index=0):
        image_header = self.image_info[index].__dict__
        image_header["version"] = self.version
        return image_header

    def save(self, target):
        if isinstance(target, Path):
            f = open(target, "wb")
        else:
            f = target

        f.write("TIM2".encode("utf-8"))
        f.write(int.to_bytes(self.version, 2, "little"))
        f.write(int.to_bytes(len(self.image_info), 2, "little"))
        f.write(b"\x00" * (f.tell() % 16))

        for i, image_info in enumerate(self.image_info):
            start_offset = f.tell()
            f.write(int.to_bytes(image_info.totalImageLength, 4, "little"))
            f.write(int.to_bytes(image_info.paletteLength, 4, "little"))
            f.write(int.to_bytes(image_info.imageDataLength, 4, "little"))
            f.write(int.to_bytes(image_info.headerLength, 2, "little"))
            f.write(int.to_bytes(image_info.colorEntries, 2, "little"))
            f.write(int.to_bytes(image_info.imageFormat, 1, "little"))
            f.write(int.to_bytes(image_info.mipmapCount, 1, "little"))
            f.write(int.to_bytes(image_info.clutFormat, 1, "little"))
            f.write(int.to_bytes(image_info.bitsPerPixel, 1, "little"))
            f.write(int.to_bytes(image_info.imageWidth, 2, "little"))
            f.write(int.to_bytes(image_info.imageHeight, 2, "little"))
            f.write(int.to_bytes(image_info.gsTEX0, 8, "little"))
            f.write(int.to_bytes(image_info.gsTEX1, 8, "little"))
            f.write(int.to_bytes(image_info.gsRegs, 8, "little"))
            f.write(int.to_bytes(image_info.gsTexClut, 8, "little"))
            end_offset = f.tell()

            padding_length = image_info.headerLength - (end_offset - start_offset)

            if padding_length > 0:
                f.write(b"\x00" * padding_length)
            else:
                f.seek(padding_length, 1)

            f.write(
                self.images[i].tobytes(
                    "raw", self.__get_image_format(image_info.bitsPerPixel)
                )
            )
