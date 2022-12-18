import json
import logging
import os
from pathlib import Path

from typer import Typer

from kingdomheartstools.helpers.TIM2 import TIM2
from kingdomheartstools.tools.archive_extract import ArchiveExtract
from kingdomheartstools.tools.archive_repack import ArchiveRepack
from kingdomheartstools.tools.ctd_compile import CTDCompile
from kingdomheartstools.tools.ctd_decompile import CTDDecompile
from kingdomheartstools.tools.exia_extract import ExiaExtract
from kingdomheartstools.tools.font_extract import FontExtract
from kingdomheartstools.tools.font_generate import FontGenerate
from kingdomheartstools.tools.l2d_build import L2DBuild
from kingdomheartstools.tools.l2d_convert import L2DConvert

app = Typer()
logger = logging.getLogger(__name__)


@app.command()
def archive_extract(input_path: str, output_path: str):
    ArchiveExtract(input_path, output_path).extract()


@app.command()
def archive_repack(input_path: str, output_path: str):
    ArchiveRepack(input_path, output_path).repack()


@app.command()
def ctd_decompile(input_path: str):
    CTDDecompile(input_path).decompile()


@app.command()
def ctd_compile(input_path: str):
    CTDCompile(input_path).compile()


@app.command()
def font_extract(input_path: str):
    FontExtract(input_path).extract()


@app.command()
def font_generate(font_folder: str):
    FontGenerate(font_folder).generate()


@app.command()
def l2d_convert(input_path: str):
    L2DConvert(input_path).convert()


@app.command()
def l2d_build(input_folder: str, original_file_path: str):
    L2DBuild(input_folder, original_file_path).build()


@app.command()
def exia_extract(input_path: str):
    ExiaExtract(input_path).extract()


@app.command()
def extract_supported(input_folder: str):
    for root, dirs, files in os.walk(input_folder):
        font_dir = False

        for file in files:
            full_path = os.path.join(root, file)
            try:
                if file.endswith(".ctd"):
                    logging.info(f"Extracting {full_path}...")
                    CTDDecompile(os.path.join(root, file)).decompile()

                if file.endswith(".inf"):
                    logging.info(f"Extracting {full_path}...")
                    font_dir = True
                    FontExtract(os.path.join(root, file)).extract()

                if file.endswith(".l2d"):
                    logging.info(f"Extracting {full_path}...")
                    L2DConvert(os.path.join(root, file)).convert()

                if file.endswith(".exia2"):
                    logging.info(f"Extracting {full_path}...")
                    ExiaExtract(os.path.join(root, file)).extract()

                if file.endswith(".tm2") and not font_dir:
                    logging.info(f"Extracting {full_path}...")

                    tim = TIM2(path=os.path.join(root, file))

                    for i in range(tim.numImages):
                        tim.get_image(i).save(
                            os.path.join(root, f"{Path(file).stem}_{i}.png")
                        )

                        with open(os.path.join(root, f"{file}_{i}.json"), "w") as f:
                            meta = tim.get_image_data(i)
                            json.dump(meta, f)
            except Exception as e:
                logger.exception(e)
