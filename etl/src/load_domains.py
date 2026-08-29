from config import RAW_DIR
from database import get_connection

from loaders.dominios import carregar_dominio_zip


def main():

    conn = get_connection()

    try:

        carregar_dominio_zip(
            conn,
            RAW_DIR,
            "Cnaes",
            "staging.cnaes",
            "public.cnaes"
        )

        carregar_dominio_zip(
            conn,
            RAW_DIR,
            "Motivos",
            "staging.motivos",
            "public.motivos_situacao"
        )

        carregar_dominio_zip(
            conn,
            RAW_DIR,
            "Municipios",
            "staging.municipios",
            "public.municipios"
        )

        carregar_dominio_zip(
            conn,
            RAW_DIR,
            "Naturezas",
            "staging.naturezas",
            "public.naturezas_juridicas"
        )

        carregar_dominio_zip(
            conn,
            RAW_DIR,
            "Paises",
            "staging.paises",
            "public.paises"
        )

        carregar_dominio_zip(
            conn,
            RAW_DIR,
            "Qualificacoes",
            "staging.qualificacoes",
            "public.qualificacoes"
        )

        print()
        print("=" * 70)
        print("DOMÍNIOS CARREGADOS COM SUCESSO")
        print("=" * 70)

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()