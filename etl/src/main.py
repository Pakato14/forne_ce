from datetime import datetime

from database import get_connection
from load import (
    carregar_empresas,
    carregar_estabelecimentos,
    carregar_socios,
)


COMPETENCIA = "2026-08"


def criar_carga(conn):

    with conn.cursor() as cur:

        cur.execute("""
            INSERT INTO public.cargas (
                competencia,
                data_inicio,
                status
            )
            VALUES (
                %s,
                %s,
                'PROCESSANDO'
            )
            RETURNING id
        """, (
            COMPETENCIA,
            datetime.now()
        ))

        carga_id = cur.fetchone()[0]

    conn.commit()

    return carga_id


def finalizar_carga(
    conn,
    carga_id,
    status="CONCLUIDO"
):

    with conn.cursor() as cur:

        cur.execute("""
            UPDATE public.cargas
            SET
                status = %s,
                data_fim = %s
            WHERE id = %s
        """, (
            status,
            datetime.now(),
            carga_id
        ))

    conn.commit()


def main():

    conn = get_connection()

    print("=" * 60)
    print("OBSERVATÓRIO EMPRESARIAL")
    print("ETL RECEITA FEDERAL")
    print(f"Competência: {COMPETENCIA}")
    print("=" * 60)

    carga_id = criar_carga(conn)

    print(f"\nCarga criada: {carga_id}")

    try:

        carregar_empresas(
            conn,
            carga_id
        )

        carregar_estabelecimentos(
            conn,
            carga_id
        )

        carregar_socios(
            conn,
            carga_id
        )

        finalizar_carga(
            conn,
            carga_id,
            "CONCLUIDO"
        )

        print("\n" + "=" * 60)
        print("IMPORTAÇÃO CONCLUÍDA")
        print("=" * 60)

    except Exception as error:

        print("\nERRO DURANTE A IMPORTAÇÃO:")
        print(error)

        conn.rollback()

        finalizar_carga(
            conn,
            carga_id,
            "ERRO"
        )

        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()