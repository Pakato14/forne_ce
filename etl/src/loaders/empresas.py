from pathlib import Path


def encontrar_arquivos_empresas(extracted_dir):

    base = Path(extracted_dir)

    arquivos = []

    for pasta in sorted(base.glob("Empresas*")):

        if not pasta.is_dir():
            continue

        for arquivo in pasta.iterdir():

            if (
                arquivo.is_file()
                and arquivo.name.endswith(".EMPRECSV")
            ):
                arquivos.append(arquivo)

    return sorted(arquivos)


def carregar_empresas(
    conn,
    extracted_dir,
    competencia,
    carga_id
):

    arquivos = encontrar_arquivos_empresas(
        extracted_dir
    )

    if not arquivos:
        raise FileNotFoundError(
            "Nenhum arquivo EMPRECSV encontrado."
        )

    print()
    print("=" * 60)
    print("CARREGAMENTO DAS EMPRESAS")
    print("=" * 60)

    total_lido = 0
    total_processado = 0
    total_erros = 0

    with conn.cursor() as cur:

        for arquivo in arquivos:

            print()
            print("-" * 60)
            print(f"Arquivo: {arquivo}")
            print("-" * 60)

            # -----------------------------------------------
            # Registrar arquivo
            # -----------------------------------------------

            cur.execute(
                """
                INSERT INTO public.carga_arquivos (
                    carga_id,
                    tipo,
                    arquivo,
                    status,
                    inicio
                )

                VALUES (
                    %s,
                    'EMPRESAS',
                    %s,
                    'PROCESSANDO',
                    CURRENT_TIMESTAMP
                )

                ON CONFLICT (
                    carga_id,
                    arquivo
                )

                DO UPDATE SET
                    status = 'PROCESSANDO',
                    inicio = CURRENT_TIMESTAMP,
                    fim = NULL,
                    mensagem_erro = NULL

                RETURNING id
                """,
                (
                    carga_id,
                    str(arquivo)
                )
            )

            arquivo_id = cur.fetchone()[0]

            conn.commit()

            registros_lidos = 0

            try:

                # -------------------------------------------
                # Limpar staging
                # -------------------------------------------

                cur.execute(
                    """
                    TRUNCATE TABLE staging.empresas
                    """
                )

                conn.commit()

                # -------------------------------------------
                # COPY
                # -------------------------------------------

                with open(
                    arquivo,
                    "r",
                    encoding="latin1",
                    newline=""
                ) as file:

                    with cur.copy(
                        """
                        COPY staging.empresas (
                            cnpj_basico,
                            razao_social,
                            natureza_juridica_codigo,
                            qualificacao_responsavel_codigo,
                            capital_social,
                            porte_codigo,
                            ente_federativo_responsavel
                        )

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

                            registros_lidos += 1

                conn.commit()

                print(
                    f"  Lidos: {registros_lidos:,}"
                )

                # -------------------------------------------
                # Inserir no destino
                # -------------------------------------------

                cur.execute(
                    """
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

                        NULLIF(
                            TRIM(cnpj_basico),
                            ''
                        ),

                        NULLIF(
                            TRIM(razao_social),
                            ''
                        ),

                        NULLIF(
                            TRIM(natureza_juridica_codigo),
                            ''
                        ),

                        NULLIF(
                            TRIM(qualificacao_responsavel_codigo),
                            ''
                        ),

                        CASE

                            WHEN
                                NULLIF(
                                    TRIM(capital_social),
                                    ''
                                ) IS NULL

                            THEN NULL

                            ELSE
                                REPLACE(
                                    REPLACE(
                                        TRIM(capital_social),
                                        '.',
                                        ''
                                    ),
                                    ',',
                                    '.'
                                )::NUMERIC(18,2)

                        END,

                        NULLIF(
                            TRIM(porte_codigo),
                            ''
                        ),

                        NULLIF(
                            TRIM(
                                ente_federativo_responsavel
                            ),
                            ''
                        ),

                        %s,

                        %s

                    FROM staging.empresas

                    ON CONFLICT (
                        cnpj_basico,
                        competencia
                    )

                    DO UPDATE SET

                        razao_social =
                            EXCLUDED.razao_social,

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

                        carga_id =
                            EXCLUDED.carga_id,

                        updated_at =
                            CURRENT_TIMESTAMP
                    """,
                    (
                        competencia,
                        carga_id
                    )
                )

                processados = cur.rowcount

                conn.commit()

                # -------------------------------------------
                # Atualizar controle
                # -------------------------------------------

                cur.execute(
                    """
                    UPDATE public.carga_arquivos

                    SET
                        status = 'CONCLUIDO',

                        fim =
                            CURRENT_TIMESTAMP,

                        registros_lidos =
                            %s,

                        registros_processados =
                            %s,

                        registros_erro =
                            0

                    WHERE id = %s
                    """,
                    (
                        registros_lidos,
                        processados,
                        arquivo_id
                    )
                )

                conn.commit()

                total_lido += registros_lidos
                total_processado += processados

                print(
                    f"  Processados: {processados:,}"
                )

            except Exception as erro:

                conn.rollback()

                total_erros += 1

                cur.execute(
                    """
                    UPDATE public.carga_arquivos

                    SET
                        status = 'ERRO',

                        fim =
                            CURRENT_TIMESTAMP,

                        registros_lidos =
                            %s,

                        registros_processados =
                            0,

                        registros_erro =
                            1,

                        mensagem_erro =
                            %s

                    WHERE id = %s
                    """,
                    (
                        registros_lidos,
                        str(erro),
                        arquivo_id
                    )
                )

                conn.commit()

                print(
                    f"ERRO no arquivo {arquivo}: {erro}"
                )

                raise

    return {
        "lidos": total_lido,
        "processados": total_processado,
        "erros": total_erros
    }