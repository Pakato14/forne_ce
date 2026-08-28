from pathlib import Path

from config import EXTRACTED_DIR


def testar_arquivos():

    grupos = [
        "Empresas",
        "Estabelecimentos",
        "Socios",
    ]

    for grupo in grupos:

        arquivos = sorted(
            Path(EXTRACTED_DIR, grupo).glob("*")
        )

        print()
        print("=" * 60)
        print(grupo)
        print("=" * 60)

        print(f"Arquivos encontrados: {len(arquivos)}")

        for arquivo in arquivos[:3]:

            print()
            print(arquivo)

            with open(
                arquivo,
                "r",
                encoding="latin1"
            ) as file:

                for i in range(2):

                    linha = file.readline()

                    if not linha:
                        break

                    print(
                        "Campos:",
                        len(linha.rstrip("\n").split(";"))
                    )


if __name__ == "__main__":
    testar_arquivos()