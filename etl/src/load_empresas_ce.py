import csv
import zipfile
import time
from decimal import Decimal, InvalidOperation

from config import RAW_DIR
from database import get_connection


COMPETENCIA = "2026-08"
CARGA_ID = 1
TAMANHO_LOTE = 10_000

def carregar_qualificacoes_validas(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT codigo
            FROM qualificacoes
        """)

        return {
            str(row[0]).strip()
            for row in cur.fetchall()
        }
        
def carregar_naturezas_validas(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT codigo
            FROM naturezas_juridicas
        """)
        return {
            str(row[0]).strip()
            for row in cur.fetchall()
        }


def carregar_cnpjs_ce(conn):
    """
    Carrega todos os CNPJs básicos da tabela cnpj_ce
    para memória.
    """

    print("Carregando lista de CNPJs do Ceará...")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT cnpj_basico
            FROM cnpj_ce
        """)

        cnpjs = {row[0] for row in cur.fetchall()}

    print(
        f"CNPJs do Ceará carregados em memória: "
        f"{len(cnpjs):,}"
    )

    return cnpjs


def converter_decimal(valor):
    """
    Converte valores no formato da Receita:

        5000,00

    para Decimal:

        5000.00
    """

    if not valor:
        return None

    valor = valor.strip()

    if not valor:
        return None

    try:
        return Decimal(valor.replace(",", "."))
    except InvalidOperation:
        return None


def inserir_lote(conn, lote):
    """
    Insere um lote de empresas.

    Retorna:
        inseridos  -> quantidade de novos registros
        duplicados -> registros que já existiam
        erro       -> quantidade de registros que falharam

    Utiliza COPY para uma tabela temporária e depois
    INSERT ... ON CONFLICT.
    """

    if not lote:
        return 0, 0, 0

    quantidade_lote = len(lote)

    try:

        with conn.cursor() as cur:

            # ----------------------------------------------------
            # Tabela temporária
            # ----------------------------------------------------

            cur.execute("""
                CREATE TEMP TABLE IF NOT EXISTS tmp_empresas (
                    cnpj_basico VARCHAR(8),
                    razao_social TEXT,
                    natureza_juridica_codigo VARCHAR(4),
                    qualificacao_responsavel_codigo VARCHAR(2),
                    capital_social NUMERIC(18,2),
                    porte_codigo VARCHAR(2),
                    ente_federativo_responsavel TEXT
                ) ON COMMIT DELETE ROWS
            """)

            # ----------------------------------------------------
            # COPY
            # ----------------------------------------------------

            with cur.copy("""
                COPY tmp_empresas (
                    cnpj_basico,
                    razao_social,
                    natureza_juridica_codigo,
                    qualificacao_responsavel_codigo,
                    capital_social,
                    porte_codigo,
                    ente_federativo_responsavel
                )
                FROM STDIN
            """) as copy:

                for registro in lote:
                    copy.write_row(registro)

            # ----------------------------------------------------
            # Inserção definitiva
            # ----------------------------------------------------

            cur.execute("""
                INSERT INTO empresas (
                    cnpj_basico,
                    razao_social,
                    natureza_juridica_codigo,
                    qualificacao_responsavel_codigo,
                    capital_social,
                    porte_codigo,
                    ente_federativo_responsavel,
                    competencia,
                    carga_id
                )
                SELECT
                    cnpj_basico,
                    razao_social,
                    natureza_juridica_codigo,
                    qualificacao_responsavel_codigo,
                    capital_social,
                    porte_codigo,
                    ente_federativo_responsavel,
                    %s,
                    %s
                FROM tmp_empresas
                ON CONFLICT (cnpj_basico, competencia)
                DO NOTHING
                RETURNING id
            """, (
                COMPETENCIA,
                CARGA_ID
            ))

            inseridos = cur.rowcount

        # --------------------------------------------------------
        # Commit
        # --------------------------------------------------------

        conn.commit()

        # Tudo que não foi inserido é duplicado
        duplicados = quantidade_lote - inseridos

        return inseridos, duplicados, 0

    except Exception as erro:

        conn.rollback()

        print()
        print("=" * 70)
        print("ERRO AO INSERIR LOTE")
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
    """
    Atualiza o controle da carga.
    """

    try:

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
                        registros_erro = %s
                    WHERE id = %s
                """, (
                    registros_lidos,
                    registros_processados,
                    registros_inseridos,
                    registros_erro,
                    CARGA_ID
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise


def processar_arquivo(arquivo, conn, cnpjs_ce, qualificacoes_validas, naturezas_validas):

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

        arquivos = z.namelist()

        csv_files = [
            nome
            for nome in arquivos
            if nome.upper().endswith(".EMPRECSV")
        ]

        if not csv_files:
            raise RuntimeError(
                f"Nenhum arquivo EMPRECSV encontrado em {arquivo}"
            )

        nome_csv = csv_files[0]

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

                    # ------------------------------------------------
                    # Validar quantidade de campos
                    # ------------------------------------------------

                    if len(linha) != 7:

                        registros_erro += 1

                        continue

                    # ------------------------------------------------
                    # CNPJ básico
                    # ------------------------------------------------

                    cnpj_basico = linha[0].strip()

                    if not cnpj_basico:
                        registros_erro += 1
                        continue

                    if cnpj_basico not in cnpjs_ce:
                        continue

                    # ------------------------------------------------
                    # Campos
                    # ------------------------------------------------

                    razao_social = (
                        linha[1].strip()
                        or None
                    )

                    natureza = (
                        linha[2].strip()
                        or None
                    )
                    if natureza and natureza not in naturezas_validas:
                        natureza = None

                    qualificacao = (
                        linha[3].strip()
                        or None
                    )
                    
                    if qualificacao and qualificacao not in qualificacoes_validas:
                        qualificacao = None

                    capital = converter_decimal(
                        linha[4]
                    )

                    porte = (
                        linha[5].strip()
                        or None
                    )

                    ente = (
                        linha[6].strip()
                        or None
                    )

                    # ------------------------------------------------
                    # Adiciona ao lote
                    # ------------------------------------------------

                    lote.append((
                        cnpj_basico,
                        razao_social,
                        natureza,
                        qualificacao,
                        capital,
                        porte,
                        ente
                    ))

                    registros_processados += 1

                    # ------------------------------------------------
                    # Processa lote
                    # ------------------------------------------------

                    if len(lote) >= TAMANHO_LOTE:

                        inseridos, duplicados, erros = inserir_lote(
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
                            registros_erro
                        )

                        print(
                            f"Linhas: {registros_lidos:,} | "
                            f"Empresas CE: {registros_processados:,} | "
                            f"Inseridas: {registros_inseridos:,} | "
                            f"Duplicadas: {registros_duplicados:,} | "
                            f"Erros: {registros_erro:,}"
                        )

                except Exception as erro:

                    registros_erro += 1

                    print(
                        f"Erro na linha "
                        f"{registros_lidos}: {erro}"
                    )

            # --------------------------------------------------------
            # Último lote
            # --------------------------------------------------------

            if lote:

                inseridos, duplicados, erros = inserir_lote(
                    conn,
                    lote
                )

                registros_inseridos += inseridos
                registros_duplicados += duplicados
                registros_erro += erros                

                lote.clear()

    tempo = time.time() - inicio

    print()
    print(f"Linhas lidas:       {registros_lidos:,}")
    print(f"Empresas do CE:     {registros_processados:,}")
    print(f"Empresas novas:     {registros_inseridos:,}")
    print(f"Duplicadas:         {registros_duplicados:,}")
    print(f"Erros:              {registros_erro:,}")
    print(f"Tempo:              {tempo / 60:.2f} minutos")

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
    print("CARGA DE EMPRESAS DO CEARÁ")
    print("=" * 70)

    print(f"Competência: {COMPETENCIA}")
    print(f"Carga ID:    {CARGA_ID}")
    print()

    conn = get_connection()

    try:
        
        # --------------------------------------------------------
        # Qualificações
        # --------------------------------------------------------
        
        qualificacoes_validas = carregar_qualificacoes_validas(conn)
        print(
            f"Qualificações válidas carregadas: "
            f"{len(qualificacoes_validas):,}"
        )
        
        # --------------------------------------------------------
        # Natureza
        # --------------------------------------------------------
        
        naturezas_validas = carregar_naturezas_validas(conn)
        print(
            f"Naturezas jurídicas válidas carregadas: "
            f"{len(naturezas_validas):,}"
            )

        # --------------------------------------------------------
        # CNPJs do Ceará
        # --------------------------------------------------------

        cnpjs_ce = carregar_cnpjs_ce(conn)

        if not cnpjs_ce:

            raise RuntimeError(
                "A tabela cnpj_ce está vazia."
            )

        # --------------------------------------------------------
        # Arquivos
        # --------------------------------------------------------

        arquivos = sorted(
            RAW_DIR.glob("Empresas*.zip")
        )

        if not arquivos:

            raise FileNotFoundError(
                f"Nenhum Empresas*.zip encontrado "
                f"em {RAW_DIR}"
            )

        print()
        print("Arquivos encontrados:")

        for arquivo in arquivos:
            print(f" - {arquivo.name}")

        print()
        print(
            f"Total: {len(arquivos)} arquivos"
        )

        # --------------------------------------------------------
        # Totais
        # --------------------------------------------------------

        total_lidos = 0
        total_processados = 0
        total_inseridos = 0
        total_duplicados = 0
        total_erros = 0

        # --------------------------------------------------------
        # Processar arquivos
        # --------------------------------------------------------

        for arquivo in arquivos:

            resultado = processar_arquivo(
                arquivo,
                conn,
                cnpjs_ce,
                qualificacoes_validas,
                naturezas_validas
            )

            (
                lidos,
                processados,
                inseridos,
                duplicados,
                erros
            ) = resultado

            total_lidos += lidos
            total_processados += processados
            total_inseridos += inseridos
            total_duplicados += duplicados
            total_erros += erros

        # --------------------------------------------------------
        # Finalizar carga
        # --------------------------------------------------------

        atualizar_carga(
            conn,
            total_lidos,
            total_processados,
            total_inseridos,
            total_erros,
            status="CONCLUIDA"
        )

        print()
        print("=" * 70)
        print("CARGA DE EMPRESAS CONCLUÍDA")
        print("=" * 70)

        print(
            f"Linhas lidas:       "
            f"{total_lidos:,}"
        )

        print(
            f"Empresas CE:        "
            f"{total_processados:,}"
        )

        print(
            f"Empresas inseridas: "
            f"{total_inseridos:,}"
        )

        print(
            f"Erros:              "
            f"{total_erros:,}"
        )

        print("=" * 70)

    except KeyboardInterrupt:

        print()
        print("=" * 70)
        print("PROCESSAMENTO INTERROMPIDO PELO USUÁRIO")
        print("=" * 70)

        conn.rollback()

        # Não marcamos como CONCLUÍDA.
        # A carga permanece EM_ANDAMENTO.

    except Exception as erro:

        conn.rollback()

        print()
        print("=" * 70)
        print("ERRO NA CARGA")
        print("=" * 70)
        print(erro)

        try:

            atualizar_carga(
                conn,
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