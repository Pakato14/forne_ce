from datetime import datetime


def iniciar_carga(conn, competencia):

    with conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO public.cargas (
                competencia,
                status,
                data_inicio
            )
            VALUES (
                %s,
                'INICIADA',
                CURRENT_TIMESTAMP
            )
            RETURNING id
            """,
            (competencia,)
        )

        carga_id = cur.fetchone()[0]

    conn.commit()

    return carga_id


def finalizar_carga(
    conn,
    carga_id,
    status,
    registros_lidos=0,
    registros_processados=0,
    registros_erro=0,
    mensagem_erro=None
):

    with conn.cursor() as cur:

        cur.execute(
            """
            UPDATE public.cargas

            SET
                status = %s,

                data_fim =
                    CURRENT_TIMESTAMP,

                registros_lidos =
                    %s,

                registros_processados =
                    %s,

                registros_erro =
                    %s,

                mensagem_erro =
                    %s

            WHERE id = %s
            """,
            (
                status,
                registros_lidos,
                registros_processados,
                registros_erro,
                mensagem_erro,
                carga_id
            )
        )

    conn.commit()


def registrar_arquivo(
    conn,
    carga_id,
    tipo,
    arquivo
):

    with conn.cursor() as cur:

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
                %s,
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
                inicio = CURRENT_TIMESTAMP

            RETURNING id
            """,
            (
                carga_id,
                tipo,
                str(arquivo)
            )
        )

        arquivo_id = cur.fetchone()[0]

    conn.commit()

    return arquivo_id


def finalizar_arquivo(
    conn,
    arquivo_id,
    status,
    registros_lidos,
    registros_processados,
    registros_erro=0,
    mensagem_erro=None
):

    with conn.cursor() as cur:

        cur.execute(
            """
            UPDATE public.carga_arquivos

            SET
                status = %s,

                fim =
                    CURRENT_TIMESTAMP,

                registros_lidos =
                    %s,

                registros_processados =
                    %s,

                registros_erro =
                    %s,

                mensagem_erro =
                    %s

            WHERE id = %s
            """,
            (
                status,
                registros_lidos,
                registros_processados,
                registros_erro,
                mensagem_erro,
                arquivo_id
            )
        )

    conn.commit()