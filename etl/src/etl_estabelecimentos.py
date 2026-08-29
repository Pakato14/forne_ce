import csv
import zipfile
import time
from datetime import datetime

from config import RAW_DIR
from database import get_connection


COMPETENCIA = "2026-08"
CARGA_ID = 2
TAMANHO_LOTE = 10_000


# ================================================================
# CARREGAR CÓDIGOS VÁLIDOS
# ================================================================

def carregar_codigos_validos(conn, tabela):
    """
    Carrega os códigos válidos de uma tabela de domínio.
    """

    with conn.cursor() as cur:

        cur.execute(f"""
            SELECT codigo
            FROM {tabela}
        """)

        return {
            str(row[0]).strip()
            for row in cur.fetchall()
            if row[0] is not None
        }


# ================================================================
# CNPJs DO CEARÁ
# ================================================================

def carregar_cnpjs_ce(conn):

    print("Carregando lista de CNPJs do Ceará...")

    with conn.cursor() as cur:

        cur.execute("""
            SELECT cnpj_basico
            FROM cnpj_ce
        """)

        cnpjs = {
            str(row[0]).strip()
            for row in cur.fetchall()
        }

    print(
        f"CNPJs do Ceará carregados em memória: "
        f"{len(cnpjs):,}"
    )

    return cnpjs


# ================================================================
# EMPRESAS
# ================================================================

def carregar_empresas(conn):

    print("Carregando empresas da competência...")

    with conn.cursor() as cur:

        cur.execute("""
            SELECT
                id,
                cnpj_basico
            FROM empresas
            WHERE competencia = %s
        """, (
            COMPETENCIA,
        ))

        empresas = {
            str(row[1]).strip(): row[0]
            for row in cur.fetchall()
        }

    print(
        f"Empresas carregadas em memória: "
        f"{len(empresas):,}"
    )

    return empresas


# ================================================================
# DATA
# ================================================================

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

def normalizar_ddd(valor):

    if not valor:
        return None

    valor = valor.strip()

    if not valor:
        return None

    # Valores usados pela Receita como preenchimento
    if valor in ("0000", "000", "00"):
        return None

    # DDD brasileiro normalmente possui 2 dígitos
    if len(valor) == 2 and valor.isdigit():
        return valor

    # Qualquer outro valor é considerado inválido
    return None

def normalizar_texto(valor):

    if not valor:
        return None

    valor = valor.strip()

    return valor if valor else None


def normalizar_telefone(valor):

    if not valor:
        return None

    valor = valor.strip()

    if not valor:
        return None

    # Preenchimento utilizado pela Receita
    if valor == "00000000":
        return None

    return valor


# ================================================================
# INSERIR LOTE
# ================================================================

def inserir_lote(conn, lote):

    if not lote:
        return 0, 0, 0

    quantidade_lote = len(lote)

    try:

        with conn.cursor() as cur:

            # ----------------------------------------------------
            # TABELA TEMPORÁRIA
            # ----------------------------------------------------

            cur.execute("""
                CREATE TEMP TABLE IF NOT EXISTS tmp_estabelecimentos (
                    empresa_id BIGINT,
                    cnpj_basico VARCHAR(8),
                    cnpj_ordem VARCHAR(4),
                    cnpj_dv VARCHAR(2),
                    cnpj_completo VARCHAR(14),
                    identificador_matriz_filial VARCHAR(1),
                    nome_fantasia TEXT,
                    situacao_cadastral_codigo VARCHAR(2),
                    data_situacao_cadastral DATE,
                    motivo_situacao_codigo VARCHAR(2),
                    nome_cidade_exterior TEXT,
                    pais_codigo VARCHAR(3),
                    data_inicio_atividade DATE,
                    cnae_principal_codigo VARCHAR(7),
                    cnae_secundario_codigo TEXT,
                    tipo_logradouro TEXT,
                    logradouro TEXT,
                    numero TEXT,
                    complemento TEXT,
                    bairro TEXT,
                    cep VARCHAR(8),
                    uf VARCHAR(2),
                    municipio_codigo VARCHAR(4),
                    ddd_1 VARCHAR(4),
                    telefone_1 VARCHAR(20),
                    ddd_2 VARCHAR(4),
                    telefone_2 VARCHAR(20),
                    fax VARCHAR(20),
                    email TEXT,
                    situacao_especial TEXT,
                    data_situacao_especial DATE
                ) ON COMMIT DELETE ROWS
            """)

            # ----------------------------------------------------
            # COPY
            # ----------------------------------------------------

            with cur.copy("""
                COPY tmp_estabelecimentos (
                    empresa_id,
                    cnpj_basico,
                    cnpj_ordem,
                    cnpj_dv,
                    cnpj_completo,
                    identificador_matriz_filial,
                    nome_fantasia,
                    situacao_cadastral_codigo,
                    data_situacao_cadastral,
                    motivo_situacao_codigo,
                    nome_cidade_exterior,
                    pais_codigo,
                    data_inicio_atividade,
                    cnae_principal_codigo,
                    cnae_secundario_codigo,
                    tipo_logradouro,
                    logradouro,
                    numero,
                    complemento,
                    bairro,
                    cep,
                    uf,
                    municipio_codigo,
                    ddd_1,
                    telefone_1,
                    ddd_2,
                    telefone_2,
                    fax,
                    email,
                    situacao_especial,
                    data_situacao_especial
                )
                FROM STDIN
            """) as copy:

                for registro in lote:

                    copy.write_row(registro)

            # ----------------------------------------------------
            # INSERÇÃO DEFINITIVA
            # ----------------------------------------------------

            cur.execute("""
                INSERT INTO estabelecimentos (
                    empresa_id,
                    cnpj_basico,
                    cnpj_ordem,
                    cnpj_dv,
                    cnpj_completo,
                    identificador_matriz_filial,
                    nome_fantasia,
                    situacao_cadastral_codigo,
                    data_situacao_cadastral,
                    motivo_situacao_codigo,
                    nome_cidade_exterior,
                    pais_codigo,
                    data_inicio_atividade,
                    cnae_principal_codigo,
                    cnae_secundario_codigo,
                    tipo_logradouro,
                    logradouro,
                    numero,
                    complemento,
                    bairro,
                    cep,
                    uf,
                    municipio_codigo,
                    ddd_1,
                    telefone_1,
                    ddd_2,
                    telefone_2,
                    fax,
                    email,
                    situacao_especial,
                    data_situacao_especial,
                    competencia,
                    carga_id
                )
                SELECT
                    empresa_id,
                    cnpj_basico,
                    cnpj_ordem,
                    cnpj_dv,
                    cnpj_completo,
                    identificador_matriz_filial,
                    nome_fantasia,
                    situacao_cadastral_codigo,
                    data_situacao_cadastral,
                    motivo_situacao_codigo,
                    nome_cidade_exterior,
                    pais_codigo,
                    data_inicio_atividade,
                    cnae_principal_codigo,
                    cnae_secundario_codigo,
                    tipo_logradouro,
                    logradouro,
                    numero,
                    complemento,
                    bairro,
                    cep,
                    uf,
                    municipio_codigo,
                    ddd_1,
                    telefone_1,
                    ddd_2,
                    telefone_2,
                    fax,
                    email,
                    situacao_especial,
                    data_situacao_especial,
                    %s,
                    %s
                FROM tmp_estabelecimentos

                ON CONFLICT (
                    cnpj_completo,
                    competencia
                )
                DO NOTHING

                RETURNING id
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
        print("ERRO AO INSERIR LOTE DE ESTABELECIMENTOS")
        print("=" * 70)
        print(
            f"Tamanho do lote: "
            f"{quantidade_lote:,}"
        )
        print(f"Erro: {erro}")
        print("=" * 70)

        return 0, 0, quantidade_lote


# ================================================================
# ATUALIZAR CARGA
# ================================================================

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

    except Exception:

        conn.rollback()

        raise


# ================================================================
# PROCESSAR ARQUIVO
# ================================================================

def processar_arquivo(
    arquivo,
    conn,
    cnpjs_ce,
    empresas,
    motivos_validos,
    paises_validos,
    municipios_validos,
    cnaes_validos
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

        arquivos = z.namelist()

        csv_files = [
            nome
            for nome in arquivos
            if nome.upper().endswith(".ESTABELE")
        ]

        if not csv_files:

            raise RuntimeError(
                f"Nenhum arquivo ESTABELE encontrado "
                f"em {arquivo}"
            )

        nome_csv = csv_files[0]

        print(
            f"Arquivo interno: {nome_csv}"
        )

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
                    # Quantidade de campos
                    # ------------------------------------------------

                    if len(linha) != 30:

                        registros_erro += 1

                        continue

                    # ------------------------------------------------
                    # CNPJ BÁSICO
                    # ------------------------------------------------

                    cnpj_basico = linha[0].strip()

                    if not cnpj_basico:

                        registros_erro += 1

                        continue

                    # ------------------------------------------------
                    # FILTRO CEARÁ
                    # ------------------------------------------------

                    if cnpj_basico not in cnpjs_ce:

                        continue

                    # ------------------------------------------------
                    # EMPRESA
                    # ------------------------------------------------

                    empresa_id = empresas.get(
                        cnpj_basico
                    )

                    if empresa_id is None:

                        # O CNPJ está em cnpj_ce,
                        # mas não existe na carga de empresas.

                        registros_erro += 1

                        continue

                    # ------------------------------------------------
                    # CNPJ
                    # ------------------------------------------------

                    cnpj_ordem = linha[1].strip()

                    cnpj_dv = linha[2].strip()

                    if not cnpj_ordem or not cnpj_dv:

                        registros_erro += 1

                        continue

                    cnpj_completo = (
                        cnpj_basico +
                        cnpj_ordem +
                        cnpj_dv
                    )

                    # ------------------------------------------------
                    # CAMPOS
                    # ------------------------------------------------

                    identificador = (
                        linha[3].strip()
                        or None
                    )

                    nome_fantasia = (
                        linha[4].strip()
                        or None
                    )

                    situacao = (
                        linha[5].strip()
                        or None
                    ) 
                    
                    if situacao and (
                        len(situacao) != 2 or
                        not situacao.isdigit()
                    ):
                        situacao = None                   

                    data_situacao = converter_data(
                        linha[6]
                    )

                    motivo = (
                        linha[7].strip()
                        or None
                    )

                    if (
                        motivo
                        and motivo not in motivos_validos
                    ):

                        motivo = None

                    nome_cidade_exterior = (
                        linha[8].strip()
                        or None
                    )

                    pais = (
                        linha[9].strip()
                        or None
                    )

                    if pais and pais not in paises_validos:

                        pais = None

                    data_inicio = converter_data(
                        linha[10]
                    )

                    cnae_principal = (
                        linha[11].strip()
                        or None
                    )

                    if (
                        cnae_principal
                        and cnae_principal not in cnaes_validos
                    ):

                        cnae_principal = None

                    cnae_secundario = (
                        linha[12].strip()
                        or None
                    )

                    tipo_logradouro = (
                        linha[13].strip()
                        or None
                    )

                    logradouro = (
                        linha[14].strip()
                        or None
                    )

                    numero = (
                        linha[15].strip()
                        or None
                    )

                    complemento = (
                        linha[16].strip()
                        or None
                    )

                    bairro = (
                        linha[17].strip()
                        or None
                    )

                    cep = (
                        linha[18].strip()
                        or None
                    )

                    uf = (
                        linha[19].strip()
                        or None
                    )

                    municipio = (
                        linha[20].strip()
                        or None
                    )

                    if (
                        municipio
                        and municipio not in municipios_validos
                    ):

                        municipio = None

                    ddd_1 = normalizar_ddd(linha[21])

                    telefone_1 = normalizar_telefone(linha[22])

                    ddd_2 = normalizar_ddd(linha[23])

                    telefone_2 = normalizar_telefone(linha[22])

                    fax = normalizar_telefone(linha[25])

                    email = (
                        linha[26].strip()
                        or None
                    )

                    situacao_especial = (
                        linha[27].strip()
                        or None
                    )

                    data_situacao_especial = converter_data(
                        linha[28]
                    )

                    # campo_30 é ignorado

                    # ------------------------------------------------
                    # LOTE
                    # ------------------------------------------------

                    lote.append((
                        empresa_id,
                        cnpj_basico,
                        cnpj_ordem,
                        cnpj_dv,
                        cnpj_completo,
                        identificador,
                        nome_fantasia,
                        situacao,
                        data_situacao,
                        motivo,
                        nome_cidade_exterior,
                        pais,
                        data_inicio,
                        cnae_principal,
                        cnae_secundario,
                        tipo_logradouro,
                        logradouro,
                        numero,
                        complemento,
                        bairro,
                        cep,
                        uf,
                        municipio,
                        ddd_1,
                        telefone_1,
                        ddd_2,
                        telefone_2,
                        fax,
                        email,
                        situacao_especial,
                        data_situacao_especial
                    ))

                    registros_processados += 1

                    # ------------------------------------------------
                    # PROCESSAR LOTE
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
                            registros_duplicados,
                            registros_erro
                        )

                        print(
                            f"Linhas: {registros_lidos:,} | "
                            f"Estabelecimentos CE: "
                            f"{registros_processados:,} | "
                            f"Inseridos: "
                            f"{registros_inseridos:,} | "
                            f"Duplicados: "
                            f"{registros_duplicados:,} | "
                            f"Erros: "
                            f"{registros_erro:,}"
                        )

                except Exception as erro:

                    registros_erro += 1

                    print(
                        f"Erro na linha "
                        f"{registros_lidos}: {erro}"
                    )

            # --------------------------------------------------------
            # ÚLTIMO LOTE
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
    print(f"Estabelecimentos CE:{registros_processados:,}")
    print(f"Estabelecimentos novos: {registros_inseridos:,}")
    print(f"Duplicados:         {registros_duplicados:,}")
    print(f"Erros:              {registros_erro:,}")
    print(f"Tempo:              {tempo / 60:.2f} minutos")

    return (
        registros_lidos,
        registros_processados,
        registros_inseridos,
        registros_duplicados,
        registros_erro
    )


# ================================================================
# MAIN
# ================================================================

def main():

    print()
    print("=" * 70)
    print("CARGA DE ESTABELECIMENTOS DO CEARÁ")
    print("=" * 70)

    print(f"Competência: {COMPETENCIA}")
    print(f"Carga ID:    {CARGA_ID}")
    print()

    conn = get_connection()

    try:

        # --------------------------------------------------------
        # CÓDIGOS DE DOMÍNIO
        # --------------------------------------------------------

        print("Carregando tabelas de domínio...")
        

        motivos_validos = carregar_codigos_validos(
            conn,
            "motivos_situacao"
        )

        paises_validos = carregar_codigos_validos(
            conn,
            "paises"
        )

        municipios_validos = carregar_codigos_validos(
            conn,
            "municipios"
        )

        cnaes_validos = carregar_codigos_validos(
            conn,
            "cnaes"
        )

        print(
            f"Motivos válidos:     "
            f"{len(motivos_validos):,}"
        )

        print(
            f"Países válidos:      "
            f"{len(paises_validos):,}"
        )

        print(
            f"Municípios válidos:  "
            f"{len(municipios_validos):,}"
        )

        print(
            f"CNAEs válidos:       "
            f"{len(cnaes_validos):,}"
        )

        # --------------------------------------------------------
        # CNPJs CE
        # --------------------------------------------------------

        cnpjs_ce = carregar_cnpjs_ce(conn)

        if not cnpjs_ce:

            raise RuntimeError(
                "A tabela cnpj_ce está vazia."
            )

        # --------------------------------------------------------
        # EMPRESAS
        # --------------------------------------------------------

        empresas = carregar_empresas(conn)

        if not empresas:

            raise RuntimeError(
                f"Nenhuma empresa encontrada "
                f"para a competência {COMPETENCIA}."
            )

        # --------------------------------------------------------
        # ARQUIVOS
        # --------------------------------------------------------

        arquivos = sorted(
            RAW_DIR.glob("Estabelecimentos*.zip")
        )

        if not arquivos:

            raise FileNotFoundError(
                f"Nenhum Estabelecimentos*.zip "
                f"encontrado em {RAW_DIR}"
            )

        print()
        print("Arquivos encontrados:")

        for arquivo in arquivos:

            print(
                f" - {arquivo.name}"
            )

        print()
        print(
            f"Total: {len(arquivos)} arquivos"
        )

        # --------------------------------------------------------
        # TOTAIS
        # --------------------------------------------------------

        total_lidos = 0
        total_processados = 0
        total_inseridos = 0
        total_duplicados = 0
        total_erros = 0

        # --------------------------------------------------------
        # PROCESSAR
        # --------------------------------------------------------

        for arquivo in arquivos:

            resultado = processar_arquivo(
                arquivo,
                conn,
                cnpjs_ce,
                empresas,
                motivos_validos,
                paises_validos,
                municipios_validos,
                cnaes_validos
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
        # FINALIZAR
        # --------------------------------------------------------

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
        print("CARGA DE ESTABELECIMENTOS CONCLUÍDA")
        print("=" * 70)

        print(
            f"Linhas lidas:          "
            f"{total_lidos:,}"
        )

        print(
            f"Estabelecimentos CE:   "
            f"{total_processados:,}"
        )

        print(
            f"Estabelecimentos novos:"
            f" {total_inseridos:,}"
        )

        print(
            f"Duplicados:            "
            f"{total_duplicados:,}"
        )

        print(
            f"Erros:                 "
            f"{total_erros:,}"
        )

        print("=" * 70)

    except KeyboardInterrupt:

        print()
        print("=" * 70)
        print("PROCESSAMENTO INTERROMPIDO PELO USUÁRIO")
        print("=" * 70)

        conn.rollback()

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