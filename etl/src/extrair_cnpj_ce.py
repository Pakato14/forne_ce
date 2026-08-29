import csv
import io
import zipfile

from config import RAW_DIR
from database import get_connection


UF_CEARA = "CE"
TAMANHO_LOTE = 100_000


def inserir_lote(conn, lote):
    """
    Insere um lote de CNPJs na tabela cnpj_ce.

    Retorna a quantidade de novos CNPJs efetivamente inseridos.
    """

    if not lote:
        return 0

    with conn.cursor() as cur:

        cur.execute("""
            CREATE TEMP TABLE IF NOT EXISTS tmp_cnpj_ce (
                cnpj_basico VARCHAR(8)
            ) ON COMMIT DELETE ROWS
        """)

        with cur.copy(
            """
            COPY tmp_cnpj_ce (cnpj_basico)
            FROM STDIN
            WITH (FORMAT CSV)
            """
        ) as copy:

            for cnpj in lote:
                copy.write_row((cnpj,))

        cur.execute("""
            INSERT INTO cnpj_ce (cnpj_basico)
            SELECT DISTINCT cnpj_basico
            FROM tmp_cnpj_ce
            ON CONFLICT (cnpj_basico)
            DO NOTHING
            RETURNING cnpj_basico
        """)

        novos = cur.fetchall()

    conn.commit()

    return len(novos)


def extrair_cnpj_ce(arquivo_zip):

    print("=" * 70)
    print("IDENTIFICANDO EMPRESAS DO CEARÁ")
    print("=" * 70)

    print(f"ZIP: {arquivo_zip}")

    total_linhas = 0
    total_ce = 0
    total_cnpj = 0

    lote = set()

    conn = get_connection()

    try:

        with zipfile.ZipFile(arquivo_zip, "r") as z:

            arquivos = [
                nome
                for nome in z.namelist()
                if nome.upper().endswith(".ESTABELE")
            ]

            if not arquivos:
                raise RuntimeError(
                    "Nenhum arquivo .ESTABELE encontrado dentro do ZIP."
                )

            nome_arquivo = arquivos[0]

            print(f"Arquivo interno: {nome_arquivo}")
            print()

            with z.open(nome_arquivo) as arquivo:

                texto = io.TextIOWrapper(
                    arquivo,
                    encoding="latin1",
                    errors="replace"
                )

                leitor = csv.reader(
                    texto,
                    delimiter=";"
                )

                for linha in leitor:

                    total_linhas += 1

                    if len(linha) < 20:
                        continue

                    cnpj_basico = linha[0].strip()
                    uf = linha[19].strip()

                    if uf != UF_CEARA:
                        continue

                    total_ce += 1

                    if len(cnpj_basico) != 8:
                        continue

                    lote.add(cnpj_basico)

                    if len(lote) >= TAMANHO_LOTE:

                        novos = inserir_lote(
                            conn,
                            lote
                        )

                        total_cnpj += novos

                        print(
                            f"Linhas analisadas: {total_linhas:,} | "
                            f"Estabelecimentos CE: {total_ce:,} | "
                            f"CNPJs processados: {total_cnpj:,}"
                        )

                        lote.clear()

                # Último lote

                if lote:

                    novos = inserir_lote(
                        conn,
                        lote
                    )

                    total_cnpj += novos

                    lote.clear()

        # Quantidade realmente existente no banco

        with conn.cursor() as cur:

            cur.execute(
                "SELECT COUNT(*) FROM cnpj_ce"
            )

            total_banco = cur.fetchone()[0]

        print()
        print("=" * 70)
        print("RESULTADO")
        print("=" * 70)

        print(
            f"Linhas analisadas:       {total_linhas:,}"
        )

        print(
            f"Estabelecimentos CE:     {total_ce:,}"
        )

        print(
            f"CNPJs enviados ao banco: {total_cnpj:,}"
        )

        print(
            f"CNPJs únicos no banco:   {total_banco:,}"
        )

        print("=" * 70)

    finally:

        conn.close()


if __name__ == "__main__":

    arquivos = sorted(
        RAW_DIR.glob("Estabelecimentos*.zip")
    )

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum ZIP de estabelecimentos encontrado em: {RAW_DIR}"
        )

    print()
    print("=" * 70)
    print("ARQUIVOS DE ESTABELECIMENTOS")
    print("=" * 70)

    for arquivo in arquivos:
        print(f" - {arquivo.name}")

    print()
    print(f"Total de arquivos: {len(arquivos)}")
    print()

    for arquivo in arquivos:

        print()
        print("#" * 70)
        print(f"PROCESSANDO: {arquivo.name}")
        print("#" * 70)

        extrair_cnpj_ce(arquivo)