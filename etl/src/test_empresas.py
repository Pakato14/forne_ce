from pathlib import Path

from config import EXTRACTED_DIR
from database import get_connection


def main():

    base = Path(EXTRACTED_DIR)

    arquivo = sorted(
        base.glob("Empresas*/*.EMPRECSV")
    )[0]

    print(f"Arquivo utilizado: {arquivo}")

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                "TRUNCATE TABLE staging.empresas"
            )

            with open(
                arquivo,
                "r",
                encoding="latin1",
                newline=""
            ) as file:

                linhas = []

                for i, linha in enumerate(file):

                    if i >= 1000:
                        break

                    linhas.append(linha)

                with cur.copy(
                    """
                    COPY staging.empresas
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        DELIMITER ';',
                        QUOTE '"'
                    )
                    """
                ) as copy:

                    for linha in linhas:
                        copy.write(linha)

            conn.commit()

            cur.execute(
                "SELECT COUNT(*) FROM staging.empresas"
            )

            total = cur.fetchone()[0]

            print(
                f"Registros carregados no staging: {total}"
            )

            cur.execute(
                """
                SELECT *
                FROM staging.empresas
                LIMIT 5
                """
            )

            for registro in cur.fetchall():
                print(registro)

    finally:

        conn.close()


if __name__ == "__main__":
    main()