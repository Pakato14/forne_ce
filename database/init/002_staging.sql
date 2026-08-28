-- =========================================================
-- STAGING CNAES
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.cnaes (
    codigo TEXT,
    descricao TEXT
);


-- =========================================================
-- STAGING MOTIVOS
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.motivos (
    codigo TEXT,
    descricao TEXT
);


-- =========================================================
-- STAGING MUNICIPIOS
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.municipios (
    codigo TEXT,
    nome TEXT
);


-- =========================================================
-- STAGING NATUREZAS
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.naturezas (
    codigo TEXT,
    descricao TEXT
);


-- =========================================================
-- STAGING PAISES
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.paises (
    codigo TEXT,
    nome TEXT
);


-- =========================================================
-- STAGING QUALIFICACOES
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.qualificacoes (
    codigo TEXT,
    descricao TEXT
);


-- =========================================================
-- STAGING EMPRESAS
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.empresas (
    cnpj_basico TEXT,
    razao_social TEXT,
    natureza_juridica_codigo TEXT,
    qualificacao_responsavel_codigo TEXT,
    capital_social TEXT,
    porte_codigo TEXT,
    ente_federativo_responsavel TEXT
);


-- =========================================================
-- STAGING ESTABELECIMENTOS
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.estabelecimentos (
    cnpj_basico TEXT,
    cnpj_ordem TEXT,
    cnpj_dv TEXT,
    identificador_matriz_filial TEXT,
    nome_fantasia TEXT,
    situacao_cadastral_codigo TEXT,
    data_situacao_cadastral TEXT,
    motivo_situacao_codigo TEXT,
    nome_cidade_exterior TEXT,
    pais_codigo TEXT,
    data_inicio_atividade TEXT,
    cnae_principal_codigo TEXT,
    cnae_secundario_codigo TEXT,
    tipo_logradouro TEXT,
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cep TEXT,
    uf TEXT,
    municipio_codigo TEXT,
    ddd_1 TEXT,
    telefone_1 TEXT,
    ddd_2 TEXT,
    telefone_2 TEXT,
    fax TEXT,
    email TEXT,
    situacao_especial TEXT,
    data_situacao_especial TEXT,
    campo_30 TEXT
);


-- =========================================================
-- STAGING SOCIOS
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.socios (
    cnpj_basico TEXT,
    tipo_socio_codigo TEXT,
    nome_socio TEXT,
    documento_socio TEXT,
    qualificacao_codigo TEXT,
    data_entrada TEXT,
    pais_codigo TEXT,
    representante_legal_documento TEXT,
    representante_legal_nome TEXT,
    qualificacao_representante_codigo TEXT,
    faixa_etaria TEXT
);


-- =========================================================
-- STAGING SIMPLES
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.simples (
    cnpj_basico TEXT,
    opcao_simples TEXT,
    data_opcao_simples TEXT,
    data_exclusao_simples TEXT,
    opcao_mei TEXT,
    data_opcao_mei TEXT,
    data_exclusao_mei TEXT
);

-- =========================================================
-- STAGING CNPJ_CE
-- =========================================================

CREATE TABLE IF NOT EXISTS staging.cnpj_ce (
    cnpj_basico VARCHAR(8)
);