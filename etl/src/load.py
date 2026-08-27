import csv
import os
from pathlib import Path

import psycopg
from tqdm import tqdm

from config import DATABASE_CONFIG, EXTRACTED_DIR


COMPETENCIA = "2026-08"


def get_connection():
    return psycopg.connect(
        host=DATABASE_CONFIG["host"],
        port=DATABASE_CONFIG["port"],
        dbname=DATABASE_CONFIG["database"],
        user=DATABASE_CONFIG["user"],
        password=DATABASE_CONFIG["password"],
    )


def encontrar_arquivos(pasta):
    return sorted(
        [
            str(path)
            for path in Path(pasta).rglob("*")
            if path.is_file()
        ]
    )


def carregar_empresas(conn, carga_id):

    arquivos = encontrar_arquivos(
        os.path.join(EXTRACTED_DIR, "Empresas")
    )

    print(f"\nEmpresas: {len(arquivos)} arquivos")

    total = 0

    with conn.cursor() as cur:

        cur.execute("TRUNCATE TABLE staging.empresas")

        for arquivo in arquivos:

            print(f"Carregando: {arquivo}")

            with open(
                arquivo,
                "r",
                encoding="latin1",
                newline=""
            ) as file:

                with cur.copy("""
                    COPY staging.empresas
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        DELIMITER ';',
                        QUOTE '"'
                    )
                """) as copy:

                    for row in file:
                        copy.write(row)

            conn.commit()

    with conn.cursor() as cur:

        cur.execute("""
            INSERT INTO public.empresas (
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
                TRIM(cnpj_basico),
                NULLIF(TRIM(razao_social), ''),
                NULLIF(TRIM(natureza_juridica_codigo), ''),
                NULLIF(TRIM(qualificacao_responsavel_codigo), ''),
                REPLACE(
                    NULLIF(TRIM(capital_social), ''),
                    ',',
                    '.'
                )::NUMERIC,
                NULLIF(TRIM(porte_codigo), ''),
                NULLIF(TRIM(ente_federativo_responsavel), ''),
                %s,
                %s
            FROM staging.empresas
            ON CONFLICT (cnpj_basico, competencia)
            DO UPDATE SET
                razao_social = EXCLUDED.razao_social,
                natureza_juridica_codigo =
                    EXCLUDED.natureza_juridica_codigo,
                qualificacao_responsavel_codigo =
                    EXCLUDED.qualificacao_responsavel_codigo,
                capital_social =
                    EXCLUDED.capital_social,
                porte_codigo =
                    EXCLUDED.porte_codigo,
                ente_federativo_responsavel =
                    EXCLUDED.ente_federativo_responsavel,
                updated_at = CURRENT_TIMESTAMP
        """, (COMPETENCIA, carga_id))

        total = cur.rowcount

    conn.commit()

    print(f"Empresas processadas: {total}")

    return total

def carregar_estabelecimentos(conn, carga_id):

    arquivos = encontrar_arquivos(
        os.path.join(EXTRACTED_DIR, "Estabelecimentos")
    )

    print(f"\nEstabelecimentos: {len(arquivos)} arquivos")

    with conn.cursor() as cur:

        cur.execute("TRUNCATE TABLE staging.estabelecimentos")

        for arquivo in arquivos:

            print(f"Carregando: {arquivo}")

            with open(
                arquivo,
                "r",
                encoding="latin1",
                newline=""
            ) as file:

                with cur.copy("""
                    COPY staging.estabelecimentos
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        DELIMITER ';',
                        QUOTE '"'
                    )
                """) as copy:

                    for row in file:
                        copy.write(row)

        conn.commit()

    with conn.cursor() as cur:

        cur.execute("""
            INSERT INTO public.estabelecimentos (
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
                e.id,

                s.cnpj_basico,
                s.cnpj_ordem,
                s.cnpj_dv,

                s.cnpj_basico ||
                s.cnpj_ordem ||
                s.cnpj_dv,

                NULLIF(TRIM(s.identificador_matriz_filial), ''),

                NULLIF(TRIM(s.nome_fantasia), ''),

                NULLIF(TRIM(s.situacao_cadastral_codigo), ''),

                CASE
                    WHEN s.data_situacao_cadastral ~ '^[0-9]{8}$'
                    THEN TO_DATE(
                        s.data_situacao_cadastral,
                        'YYYYMMDD'
                    )
                END,

                NULLIF(TRIM(s.motivo_situacao_codigo), ''),

                NULLIF(TRIM(s.nome_cidade_exterior), ''),

                NULLIF(TRIM(s.pais_codigo), ''),

                CASE
                    WHEN s.data_inicio_atividade ~ '^[0-9]{8}$'
                    THEN TO_DATE(
                        s.data_inicio_atividade,
                        'YYYYMMDD'
                    )
                END,

                NULLIF(TRIM(s.cnae_principal_codigo), ''),

                NULLIF(TRIM(s.cnae_secundario_codigo), ''),

                NULLIF(TRIM(s.tipo_logradouro), ''),

                NULLIF(TRIM(s.logradouro), ''),

                NULLIF(TRIM(s.numero), ''),

                NULLIF(TRIM(s.complemento), ''),

                NULLIF(TRIM(s.bairro), ''),

                NULLIF(TRIM(s.cep), ''),

                NULLIF(TRIM(s.uf), ''),

                NULLIF(TRIM(s.municipio_codigo), ''),

                NULLIF(TRIM(s.ddd_1), ''),

                NULLIF(TRIM(s.telefone_1), ''),

                NULLIF(TRIM(s.ddd_2), ''),

                NULLIF(TRIM(s.telefone_2), ''),

                NULLIF(TRIM(s.fax), ''),

                NULLIF(TRIM(s.email), ''),

                NULLIF(TRIM(s.situacao_especial), ''),

                CASE
                    WHEN s.data_situacao_especial ~ '^[0-9]{8}$'
                    THEN TO_DATE(
                        s.data_situacao_especial,
                        'YYYYMMDD'
                    )
                END,

                %s,
                %s

            FROM staging.estabelecimentos s

            INNER JOIN public.empresas e
                ON e.cnpj_basico = s.cnpj_basico
                AND e.competencia = %s

            ON CONFLICT (
                cnpj_completo,
                competencia
            )
            DO UPDATE SET
                nome_fantasia =
                    EXCLUDED.nome_fantasia,

                situacao_cadastral_codigo =
                    EXCLUDED.situacao_cadastral_codigo,

                data_situacao_cadastral =
                    EXCLUDED.data_situacao_cadastral,

                cnae_principal_codigo =
                    EXCLUDED.cnae_principal_codigo,

                cnae_secundario_codigo =
                    EXCLUDED.cnae_secundario_codigo,

                email =
                    EXCLUDED.email,

                telefone_1 =
                    EXCLUDED.telefone_1,

                telefone_2 =
                    EXCLUDED.telefone_2,

                updated_at = CURRENT_TIMESTAMP
        """, (
            COMPETENCIA,
            carga_id,
            COMPETENCIA
        ))

        total = cur.rowcount

    conn.commit()

    print(f"Estabelecimentos processados: {total}")

    return total

def carregar_socios(conn, carga_id):

    arquivos = encontrar_arquivos(
        os.path.join(EXTRACTED_DIR, "Socios")
    )

    print(f"\nSócios: {len(arquivos)} arquivos")

    with conn.cursor() as cur:

        cur.execute("TRUNCATE TABLE staging.socios")

        for arquivo in arquivos:

            print(f"Carregando: {arquivo}")

            with open(
                arquivo,
                "r",
                encoding="latin1",
                newline=""
            ) as file:

                with cur.copy("""
                    COPY staging.socios
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        DELIMITER ';',
                        QUOTE '"'
                    )
                """) as copy:

                    for row in file:
                        copy.write(row)

        conn.commit()

    with conn.cursor() as cur:

        cur.execute("""
            INSERT INTO public.socios (
                empresa_id,
                tipo_socio_codigo,
                nome_socio,
                documento_socio,
                qualificacao_codigo,
                data_entrada,
                pais_codigo,
                representante_legal_documento,
                representante_legal_nome,
                qualificacao_representante_codigo,
                faixa_etaria,
                competencia,
                carga_id
            )
            SELECT
                e.id,

                NULLIF(TRIM(s.tipo_socio_codigo), ''),

                NULLIF(TRIM(s.nome_socio), ''),

                NULLIF(TRIM(s.documento_socio), ''),

                NULLIF(TRIM(s.qualificacao_codigo), ''),

                CASE
                    WHEN s.data_entrada ~ '^[0-9]{8}$'
                    THEN TO_DATE(
                        s.data_entrada,
                        'YYYYMMDD'
                    )
                END,

                NULLIF(TRIM(s.pais_codigo), ''),

                NULLIF(
                    TRIM(s.representante_legal_documento),
                    ''
                ),

                NULLIF(
                    TRIM(s.representante_legal_nome),
                    ''
                ),

                NULLIF(
                    TRIM(s.qualificacao_representante_codigo),
                    ''
                ),

                NULLIF(TRIM(s.faixa_etaria), ''),

                %s,

                %s

            FROM staging.socios s

            INNER JOIN public.empresas e
                ON e.cnpj_basico = s.cnpj_basico
                AND e.competencia = %s
        """, (
            COMPETENCIA,
            carga_id,
            COMPETENCIA
        ))

        total = cur.rowcount

    conn.commit()

    print(f"Sócios processados: {total}")

    return total