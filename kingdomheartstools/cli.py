from typer import Typer

from kingdomheartstools.tools.archive_extract import ArchiveExtract
from kingdomheartstools.tools.archive_repack import ArchiveRepack
from kingdomheartstools.tools.ctd_compile import CTDCompile
from kingdomheartstools.tools.ctd_decompile import CTDDecompile
from kingdomheartstools.tools.font_extract import FontExtract
from kingdomheartstools.tools.font_generate import FontGenerate
from kingdomheartstools.tools.l2d_build import L2DBuild
from kingdomheartstools.tools.l2d_convert import L2DConvert

app = Typer()


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
