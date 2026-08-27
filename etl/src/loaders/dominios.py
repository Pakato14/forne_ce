from pathlib import Path


def encontrar_arquivo(pasta):

    arquivos = [
        arquivo
        for arquivo in Path(pasta).rglob("*")
        if arquivo.is_file()
    ]

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo encontrado em {pasta}"
        )

    return arquivos[0]


def carregar_dominio(
    conn,
    pasta,
    tabela_staging,
    tabela_destino,
    competencia=None
):

    arquivo = encontrar_arquivo(pasta)

    print(f"\nCarregando domínio: {tabela_destino}")
    print(f"Arquivo: {arquivo}")

    with conn.cursor() as cur:

        cur.execute(
            f"TRUNCATE TABLE {tabela_staging}"
        )

        with open(
            arquivo,
            "r",
            encoding="latin1",
            newline=""
        ) as file:

            with cur.copy(
                f"""
                COPY {tabela_staging}
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    DELIMITER ';',
                    QUOTE '"'
                )
                """
            ) as copy:

                for linha in file:
                    copy.write(linha)

        conn.commit()

        if tabela_destino == "public.cnaes":

            cur.execute("""
                INSERT INTO public.cnaes (
                    codigo,
                    descricao
                )
                SELECT
                    TRIM(codigo),
                    TRIM(descricao)
                FROM staging.cnaes
                ON CONFLICT (codigo)
                DO UPDATE SET
                    descricao = EXCLUDED.descricao
            """)

        elif tabela_destino == "public.motivos_situacao":

            cur.execute("""
                INSERT INTO public.motivos_situacao (
                    codigo,
                    descricao
                )
                SELECT
                    TRIM(codigo),
                    TRIM(descricao)
                FROM staging.motivos
                ON CONFLICT (codigo)
                DO UPDATE SET
                    descricao = EXCLUDED.descricao
            """)

        elif tabela_destino == "public.municipios":

            cur.execute("""
                INSERT INTO public.municipios (
                    codigo,
                    nome
                )
                SELECT
                    TRIM(codigo),
                    TRIM(nome)
                FROM staging.municipios
                ON CONFLICT (codigo)
                DO UPDATE SET
                    nome = EXCLUDED.nome
            """)

        elif tabela_destino == "public.naturezas_juridicas":

            cur.execute("""
                INSERT INTO public.naturezas_juridicas (
                    codigo,
                    descricao
                )
                SELECT
                    TRIM(codigo),
                    TRIM(descricao)
                FROM staging.naturezas
                ON CONFLICT (codigo)
                DO UPDATE SET
                    descricao = EXCLUDED.descricao
            """)

        elif tabela_destino == "public.paises":

            cur.execute("""
                INSERT INTO public.paises (
                    codigo,
                    nome
                )
                SELECT
                    TRIM(codigo),
                    TRIM(nome)
                FROM staging.paises
                ON CONFLICT (codigo)
                DO UPDATE SET
                    nome = EXCLUDED.nome
            """)

        elif tabela_destino == "public.qualificacoes":

            cur.execute("""
                INSERT INTO public.qualificacoes (
                    codigo,
                    descricao
                )
                SELECT
                    TRIM(codigo),
                    TRIM(descricao)
                FROM staging.qualificacoes
                ON CONFLICT (codigo)
                DO UPDATE SET
                    descricao = EXCLUDED.descricao
            """)

        else:
            raise ValueError(
                f"Tabela não suportada: {tabela_destino}"
            )

        total = cur.rowcount

    conn.commit()

    print(
        f"{tabela_destino}: {total} registros processados"
    )

    return total