from io import BytesIO

from PIL import Image

from ..common.tim.ImageData import ImageData


class TIM2:

    image_info = []
    images = []

    def __init__(self, **kwargs) -> None:
        if kwargs.get("path"):
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

        self.tim2.seek(0x10)

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
                "RGBA",
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

    def save(self, path):
        with open(path, "wb") as f:
            f.write("TIM2".encode("utf-8"))
            f.write(int.to_bytes(self.version, 2, "little"))
            f.write(int.to_bytes(len(self.image_info), 2, "little"))
            f.write(b"\x00" * 8)

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
                f.write(b"\x00" * padding_length)
                f.write(self.images[i].tobytes("raw", "RGBA"))
