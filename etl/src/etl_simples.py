import csv
import zipfile
import time
from datetime import datetime

from config import RAW_DIR
from database import get_connection


COMPETENCIA = "2026-08"
CARGA_ID = 4
TAMANHO_LOTE = 10_000


def carregar_cnpjs_ce(conn):

    print("Carregando CNPJs do Ceará...")

    with conn.cursor() as cur:

        cur.execute("""
            SELECT cnpj_basico
            FROM cnpj_ce
        """)

        cnpjs = {
            str(row[0]).strip()
            for row in cur.fetchall()
            if row[0] is not None
        }

    print(f"CNPJs CE carregados: {len(cnpjs):,}")

    return cnpjs


def converter_data(valor):

    if not valor:
        return None

    valor = valor.strip()

    if not valor:
        return None

    try:
        return datetime.strptime(
            valor,
            "%Y%m%d"
        ).date()

    except ValueError:
        return None


def normalizar_texto(valor):

    if valor is None:
        return None

    valor = valor.strip()

    return valor or None


def inserir_lote(conn, lote):

    if not lote:
        return 0, 0, 0

    quantidade_lote = len(lote)

    try:

        with conn.cursor() as cur:

            cur.execute("""
                CREATE TEMP TABLE IF NOT EXISTS tmp_simples (
                    cnpj_basico VARCHAR(8),
                    opcao_simples VARCHAR(1),
                    data_opcao_simples DATE,
                    data_exclusao_simples DATE,
                    opcao_mei VARCHAR(1),
                    data_opcao_mei DATE,
                    data_exclusao_mei DATE
                )
                ON COMMIT DELETE ROWS
            """)

            with cur.copy("""
                COPY tmp_simples (
                    cnpj_basico,
                    opcao_simples,
                    data_opcao_simples,
                    data_exclusao_simples,
                    opcao_mei,
                    data_opcao_mei,
                    data_exclusao_mei
                )
                FROM STDIN
            """) as copy:

                for registro in lote:
                    copy.write_row(registro)

            cur.execute("""
                INSERT INTO simples (
                    cnpj_basico,
                    opcao_simples,
                    data_opcao_simples,
                    data_exclusao_simples,
                    opcao_mei,
                    data_opcao_mei,
                    data_exclusao_mei,
                    competencia,
                    carga_id
                )
                SELECT
                    cnpj_basico,
                    opcao_simples,
                    data_opcao_simples,
                    data_exclusao_simples,
                    opcao_mei,
                    data_opcao_mei,
                    data_exclusao_mei,
                    %s,
                    %s
                FROM tmp_simples
                ON CONFLICT (
                    cnpj_basico,
                    competencia
                )
                DO NOTHING
                RETURNING cnpj_basico
            """, (
                COMPETENCIA,
                CARGA_ID
            ))

            inseridos = cur.rowcount

        conn.commit()

        duplicados = quantidade_lote - inseridos

        return inseridos, duplicados, 0

    except Exception as erro:

        conn.rollback()

        print()
        print("=" * 70)
        print("ERRO AO INSERIR LOTE DO SIMPLES")
        print("=" * 70)
        print(f"Tamanho do lote: {quantidade_lote:,}")
        print(f"Erro: {erro}")
        print("=" * 70)

        return 0, 0, quantidade_lote


def atualizar_carga(
    conn,
    registros_lidos,
    registros_processados,
    registros_inseridos,
    registros_duplicados,
    registros_erro=0,
    status=None,
    mensagem_erro=None
):

    with conn.cursor() as cur:

        if status:

            cur.execute("""
                UPDATE cargas
                SET
                    data_fim = CURRENT_TIMESTAMP,
                    status = %s,
                    registros_lidos = %s,
                    registros_processados = %s,
                    registros_inseridos = %s,
                    registros_duplicados = %s,
                    registros_erro = %s,
                    mensagem_erro = %s
                WHERE id = %s
            """, (
                status,
                registros_lidos,
                registros_processados,
                registros_inseridos,
                registros_duplicados,
                registros_erro,
                mensagem_erro,
                CARGA_ID
            ))

        else:

            cur.execute("""
                UPDATE cargas
                SET
                    registros_lidos = %s,
                    registros_processados = %s,
                    registros_inseridos = %s,
                    registros_duplicados = %s,
                    registros_erro = %s
                WHERE id = %s
            """, (
                registros_lidos,
                registros_processados,
                registros_inseridos,
                registros_duplicados,
                registros_erro,
                CARGA_ID
            ))

    conn.commit()


def processar_arquivo(
    arquivo,
    conn,
    cnpjs_ce
):

    print()
    print("=" * 70)
    print(f"PROCESSANDO: {arquivo.name}")
    print("=" * 70)

    inicio = time.time()

    registros_lidos = 0
    registros_processados = 0
    registros_inseridos = 0
    registros_duplicados = 0
    registros_erro = 0

    lote = []

    with zipfile.ZipFile(arquivo, "r") as z:

        arquivos_csv = [
            nome
            for nome in z.namelist()
            if ".SIMPLES.CSV." in nome.upper()
        ]

        if not arquivos_csv:
            raise RuntimeError(
                f"Nenhum arquivo SIMPLES encontrado em {arquivo}"
            )

        nome_csv = arquivos_csv[0]

        print(f"Arquivo interno: {nome_csv}")

        with z.open(nome_csv) as arquivo_csv:

            texto = (
                linha.decode("latin1")
                for linha in arquivo_csv
            )

            leitor = csv.reader(
                texto,
                delimiter=";",
                quotechar='"'
            )

            for linha in leitor:

                registros_lidos += 1

                try:

                    if len(linha) != 7:
                        registros_erro += 1
                        continue

                    cnpj_basico = linha[0].strip()

                    if not cnpj_basico:
                        registros_erro += 1
                        continue

                    if cnpj_basico not in cnpjs_ce:
                        continue

                    opcao_simples = normalizar_texto(
                        linha[1]
                    )

                    data_opcao_simples = converter_data(
                        linha[2]
                    )

                    data_exclusao_simples = converter_data(
                        linha[3]
                    )

                    opcao_mei = normalizar_texto(
                        linha[4]
                    )

                    data_opcao_mei = converter_data(
                        linha[5]
                    )

                    data_exclusao_mei = converter_data(
                        linha[6]
                    )

                    lote.append((
                        cnpj_basico,
                        opcao_simples,
                        data_opcao_simples,
                        data_exclusao_simples,
                        opcao_mei,
                        data_opcao_mei,
                        data_exclusao_mei
                    ))

                    registros_processados += 1

                    if len(lote) >= TAMANHO_LOTE:

                        (
                            inseridos,
                            duplicados,
                            erros
                        ) = inserir_lote(
                            conn,
                            lote
                        )

                        registros_inseridos += inseridos
                        registros_duplicados += duplicados
                        registros_erro += erros

                        lote.clear()

                        atualizar_carga(
                            conn,
                            registros_lidos,
                            registros_processados,
                            registros_inseridos,
                            registros_duplicados,
                            registros_erro
                        )

                        print(
                            f"Linhas: {registros_lidos:,} | "
                            f"Simples CE: {registros_processados:,} | "
                            f"Inseridos: {registros_inseridos:,} | "
                            f"Duplicados: {registros_duplicados:,} | "
                            f"Erros: {registros_erro:,}"
                        )

                except Exception as erro:

                    registros_erro += 1

                    print(
                        f"Erro na linha "
                        f"{registros_lidos}: {erro}"
                    )

            if lote:

                (
                    inseridos,
                    duplicados,
                    erros
                ) = inserir_lote(
                    conn,
                    lote
                )

                registros_inseridos += inseridos
                registros_duplicados += duplicados
                registros_erro += erros

                lote.clear()

    tempo = time.time() - inicio

    print()
    print(f"Linhas lidas:   {registros_lidos:,}")
    print(f"Simples CE:     {registros_processados:,}")
    print(f"Inseridos:      {registros_inseridos:,}")
    print(f"Duplicados:     {registros_duplicados:,}")
    print(f"Erros:          {registros_erro:,}")
    print(f"Tempo:          {tempo / 60:.2f} minutos")

    return (
        registros_lidos,
        registros_processados,
        registros_inseridos,
        registros_duplicados,
        registros_erro
    )


def main():

    print()
    print("=" * 70)
    print("CARGA DO SIMPLES NACIONAL / MEI - CEARÁ")
    print("=" * 70)

    print(f"Competência: {COMPETENCIA}")
    print(f"Carga ID:    {CARGA_ID}")
    print()

    conn = get_connection()

    try:

        cnpjs_ce = carregar_cnpjs_ce(conn)

        arquivo = RAW_DIR / "Simples.zip"

        if not arquivo.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {arquivo}"
            )

        (
            total_lidos,
            total_processados,
            total_inseridos,
            total_duplicados,
            total_erros
        ) = processar_arquivo(
            arquivo,
            conn,
            cnpjs_ce
        )

        atualizar_carga(
            conn,
            total_lidos,
            total_processados,
            total_inseridos,
            total_duplicados,
            total_erros,
            status="CONCLUIDA"
        )

        print()
        print("=" * 70)
        print("CARGA DO SIMPLES CONCLUÍDA")
        print("=" * 70)

        print(f"Linhas lidas:   {total_lidos:,}")
        print(f"Simples CE:     {total_processados:,}")
        print(f"Inseridos:      {total_inseridos:,}")
        print(f"Duplicados:     {total_duplicados:,}")
        print(f"Erros:          {total_erros:,}")

        print("=" * 70)

    except KeyboardInterrupt:

        conn.rollback()

        print()
        print("Processamento interrompido.")

    except Exception as erro:

        conn.rollback()

        print()
        print("=" * 70)
        print("ERRO NA CARGA DO SIMPLES")
        print("=" * 70)
        print(erro)

        try:

            atualizar_carga(
                conn,
                0,
                0,
                0,
                0,
                1,
                status="ERRO",
                mensagem_erro=str(erro)
            )

        except Exception:
            pass

        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()