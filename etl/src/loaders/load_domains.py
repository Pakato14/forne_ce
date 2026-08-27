import os

from database import get_connection
from config import EXTRACTED_DIR

from loaders.dominios import carregar_dominio


def main():

    conn = get_connection()

    try:

        carregar_dominio(
            conn,
            os.path.join(
                EXTRACTED_DIR,
                "Cnaes"
            ),
            "staging.cnaes",
            "public.cnaes"
        )

        carregar_dominio(
            conn,
            os.path.join(
                EXTRACTED_DIR,
                "Motivos"
            ),
            "staging.motivos",
            "public.motivos_situacao"
        )

        carregar_dominio(
            conn,
            os.path.join(
                EXTRACTED_DIR,
                "Municipios"
            ),
            "staging.municipios",
            "public.municipios"
        )

        carregar_dominio(
            conn,
            os.path.join(
                EXTRACTED_DIR,
                "Naturezas"
            ),
            "staging.naturezas",
            "public.naturezas_juridicas"
        )

        carregar_dominio(
            conn,
            os.path.join(
                EXTRACTED_DIR,
                "Paises"
            ),
            "staging.paises",
            "public.paises"
        )

        carregar_dominio(
            conn,
            os.path.join(
                EXTRACTED_DIR,
                "Qualificacoes"
            ),
            "staging.qualificacoes",
            "public.qualificacoes"
        )

        print("\nDomínios carregados com sucesso.")

    finally:

        conn.close()


if __name__ == "__main__":
    main()