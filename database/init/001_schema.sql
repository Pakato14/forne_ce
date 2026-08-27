CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;


-- =====================================================
-- CARGAS
-- =====================================================

CREATE TABLE IF NOT EXISTS public.cargas (
    id BIGSERIAL PRIMARY KEY,

    competencia VARCHAR(7) NOT NULL,

    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,

    status VARCHAR(30) NOT NULL,

    arquivo VARCHAR(255),
    tipo_arquivo VARCHAR(100),

    registros_lidos BIGINT DEFAULT 0,
    registros_processados BIGINT DEFAULT 0,
    registros_inseridos BIGINT DEFAULT 0,
    registros_atualizados BIGINT DEFAULT 0,
    registros_erro BIGINT DEFAULT 0,

    mensagem_erro TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- EMPRESAS
-- =====================================================

CREATE TABLE IF NOT EXISTS public.empresas (
    id BIGSERIAL PRIMARY KEY,

    cnpj_basico VARCHAR(8) NOT NULL UNIQUE,

    razao_social TEXT,

    natureza_juridica_codigo VARCHAR(4),

    qualificacao_responsavel_codigo VARCHAR(2),

    capital_social NUMERIC(18,2),

    porte_codigo VARCHAR(2),

    ente_federativo_responsavel TEXT,

    competencia VARCHAR(7),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- ESTABELECIMENTOS
-- =====================================================

CREATE TABLE IF NOT EXISTS public.estabelecimentos (
    id BIGSERIAL PRIMARY KEY,

    empresa_id BIGINT NOT NULL
        REFERENCES public.empresas(id)
        ON DELETE CASCADE,

    cnpj_completo VARCHAR(14) NOT NULL UNIQUE,

    cnpj_ordem VARCHAR(4),
    cnpj_dv VARCHAR(2),

    identificador_matriz_filial VARCHAR(1),

    nome_fantasia TEXT,

    situacao_cadastral_codigo VARCHAR(2),

    data_situacao_cadastral DATE,

    motivo_situacao_codigo VARCHAR(2),

    data_inicio_atividade DATE,

    cnae_principal_codigo VARCHAR(7),

    tipo_logradouro TEXT,
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,

    bairro TEXT,
    cep VARCHAR(8),

    municipio_codigo VARCHAR(7),
    uf VARCHAR(2),

    ddd_1 VARCHAR(3),
    telefone_1 VARCHAR(20),

    ddd_2 VARCHAR(3),
    telefone_2 VARCHAR(20),

    email TEXT,

    situacao_especial TEXT,
    data_situacao_especial DATE,

    competencia VARCHAR(7),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- SÓCIOS
-- =====================================================

CREATE TABLE IF NOT EXISTS public.socios (
    id BIGSERIAL PRIMARY KEY,

    empresa_id BIGINT NOT NULL
        REFERENCES public.empresas(id)
        ON DELETE CASCADE,

    tipo_socio_codigo VARCHAR(2),

    documento_socio VARCHAR(20),

    nome_socio TEXT,

    qualificacao_codigo VARCHAR(2),

    data_entrada DATE,

    faixa_etaria VARCHAR(2),

    competencia VARCHAR(7),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- ÍNDICES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_empresas_razao_social
ON public.empresas
USING gin (razao_social gin_trgm_ops);


CREATE INDEX IF NOT EXISTS idx_estabelecimentos_cnae
ON public.estabelecimentos(cnae_principal_codigo);


CREATE INDEX IF NOT EXISTS idx_estabelecimentos_municipio
ON public.estabelecimentos(municipio_codigo);


CREATE INDEX IF NOT EXISTS idx_estabelecimentos_uf
ON public.estabelecimentos(uf);


CREATE INDEX IF NOT EXISTS idx_estabelecimentos_situacao
ON public.estabelecimentos(situacao_cadastral_codigo);


CREATE INDEX IF NOT EXISTS idx_estabelecimentos_nome_fantasia
ON public.estabelecimentos
USING gin (nome_fantasia gin_trgm_ops);


CREATE INDEX IF NOT EXISTS idx_socios_empresa
ON public.socios(empresa_id);


CREATE INDEX IF NOT EXISTS idx_socios_documento
ON public.socios(documento_socio);


CREATE INDEX IF NOT EXISTS idx_socios_nome
ON public.socios
USING gin (nome_socio gin_trgm_ops);