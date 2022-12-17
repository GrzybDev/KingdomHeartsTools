from kingdomheartstools.tools.archive_extract import ArchiveExtract
from typer import Typer

from kingdomheartstools.tools.archive_repack import ArchiveRepack

app = Typer()


@app.command()
def extract(input_path: str, output_path: str):
    ArchiveExtract(input_path, output_path).extract()


@app.command()
def repack(input_path: str, output_path: str):
    ArchiveRepack(input_path, output_path).repack()
