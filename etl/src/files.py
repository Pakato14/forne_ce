from pathlib import Path

from config import EXTRACTED_DIR


def arquivos_da_familia(prefixo: str):

    arquivos = []

    base = Path(EXTRACTED_DIR)

    for pasta in base.glob(f"{prefixo}*"):

        if not pasta.is_dir():
            continue

        for arquivo in pasta.iterdir():

            if arquivo.is_file():
                arquivos.append(arquivo)

    return sorted(arquivos)