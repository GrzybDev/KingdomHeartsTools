from typer import Typer

from kingdomheartstools.tools.archive_extract import ArchiveExtract
from kingdomheartstools.tools.archive_repack import ArchiveRepack
from kingdomheartstools.tools.ctd_compile import CTDCompile
from kingdomheartstools.tools.ctd_decompile import CTDDecompile

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
