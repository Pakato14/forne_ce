from pathlib import Path
from zipfile import ZipFile


def encontrar_zips(base_dir, prefixo):

    base = Path(base_dir)

    arquivos = sorted(
        base.glob(f"{prefixo}*.zip")
    )

    return arquivos


def ler_zip_linhas(arquivo_zip):

    with ZipFile(arquivo_zip, "r") as z:

        arquivos = z.namelist()

        if not arquivos:
            return

        # Normalmente existe apenas um CSV
        nome_arquivo = arquivos[0]

        print(
            f"  Arquivo interno: {nome_arquivo}"
        )

        with z.open(nome_arquivo) as arquivo:

            for linha in arquivo:

                yield linha.decode(
                    "latin1"
                ).rstrip("\r\n")