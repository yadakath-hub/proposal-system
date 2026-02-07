-- =============================================================================
-- AI Proposal Generator - Database Initialization Script
-- PostgreSQL 16 with pgvector Extension
-- =============================================================================

-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- ENUM Types
-- =============================================================================

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('Admin', 'Editor', 'Reviewer', 'Viewer');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE project_role AS ENUM ('Owner', 'Manager', 'Writer', 'Reviewer');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE project_status AS ENUM ('Draft', 'InProgress', 'Review', 'Completed', 'Archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE section_status AS ENUM ('NotStarted', 'Writing', 'Review', 'Approved', 'Locked');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE version_source AS ENUM ('Human', 'GPT4', 'GPT4o', 'GPT4oMini', 'Gemini15Pro', 'Gemini15Flash', 'Gemini20Flash', 'Imported');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE embedding_source AS ENUM ('Template', 'HistoricalProposal', 'TenderDocument', 'Section', 'ProjectAsset');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE template_type AS ENUM ('CoverPage', 'TOC', 'Chapter', 'Appendix', 'FullDoc', 'Header', 'Footer');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE asset_type AS ENUM ('Image', 'Chart', 'Table', 'Diagram', 'Attachment');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- Tables
-- =============================================================================

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'Viewer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    avatar_url VARCHAR(500),
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    tender_number VARCHAR(100),
    tender_pdf_path VARCHAR(500),
    deadline DATE,
    status project_status NOT NULL DEFAULT 'Draft',
    max_token_budget INT NOT NULL DEFAULT 1000000,
    used_tokens INT NOT NULL DEFAULT 0,
    budget_alert_threshold DECIMAL(3,2) NOT NULL DEFAULT 0.80,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);

-- Project Members
CREATE TABLE IF NOT EXISTS project_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_role project_role NOT NULL DEFAULT 'Reviewer',
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user ON project_members(user_id);

-- Sections (Chapter Tree)
CREATE TABLE IF NOT EXISTS sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    chapter_number VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    requirement_text TEXT,
    sort_order INT NOT NULL DEFAULT 0,
    depth_level INT NOT NULL DEFAULT 0,
    estimated_pages INT DEFAULT 1,
    assigned_to UUID REFERENCES users(id),
    status section_status NOT NULL DEFAULT 'NotStarted',
    word_style_name VARCHAR(100),
    docx_template_tag VARCHAR(100),
    current_version_id UUID,
    locked_by UUID REFERENCES users(id),
    locked_at TIMESTAMP WITH TIME ZONE,
    lock_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, chapter_number)
);

CREATE INDEX IF NOT EXISTS idx_sections_project ON sections(project_id);
CREATE INDEX IF NOT EXISTS idx_sections_parent ON sections(parent_id);

-- Section Versions
CREATE TABLE IF NOT EXISTS section_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content TEXT NOT NULL,
    content_html TEXT,
    source_type version_source NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    persona_id UUID,
    prompt_used TEXT,
    generation_params JSONB DEFAULT '{}'::jsonb,
    is_continuation_of UUID REFERENCES section_versions(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    is_final BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(section_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_section_versions_section ON section_versions(section_id);

-- Add FK from sections to section_versions
ALTER TABLE sections DROP CONSTRAINT IF EXISTS fk_sections_current_version;
ALTER TABLE sections ADD CONSTRAINT fk_sections_current_version 
    FOREIGN KEY (current_version_id) REFERENCES section_versions(id) ON DELETE SET NULL;

-- Project Assets
CREATE TABLE IF NOT EXISTS project_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    mime_type VARCHAR(100),
    asset_type asset_type NOT NULL DEFAULT 'Image',
    caption TEXT,
    alt_text VARCHAR(500),
    asset_tag VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_assets_project ON project_assets(project_id);

-- Templates
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type template_type NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    preview_image_path VARCHAR(500),
    tag_schema JSONB DEFAULT '[]'::jsonb,
    style_config JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Project Templates
CREATE TABLE IF NOT EXISTS project_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    usage_type VARCHAR(50) NOT NULL DEFAULT 'Main',
    priority INT NOT NULL DEFAULT 0,
    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, template_id)
);

-- AI Personas
CREATE TABLE IF NOT EXISTS ai_personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    preferred_model VARCHAR(50) NOT NULL DEFAULT 'gpt-4o',
    parameters JSONB DEFAULT '{}'::jsonb,
    default_max_tokens INT NOT NULL DEFAULT 4096,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add FK from section_versions to ai_personas
ALTER TABLE section_versions DROP CONSTRAINT IF EXISTS fk_section_versions_persona;
ALTER TABLE section_versions ADD CONSTRAINT fk_section_versions_persona 
    FOREIGN KEY (persona_id) REFERENCES ai_personas(id) ON DELETE SET NULL;

-- Document Embeddings (RAG)
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type embedding_source NOT NULL,
    source_id UUID NOT NULL,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(source_type, source_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw ON document_embeddings 
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON document_embeddings(source_type, source_id);

-- Usage Logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    section_id UUID REFERENCES sections(id) ON DELETE SET NULL,
    version_id UUID REFERENCES section_versions(id) ON DELETE SET NULL,
    persona_id UUID REFERENCES ai_personas(id) ON DELETE SET NULL,
    model_used VARCHAR(50) NOT NULL,
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    total_tokens INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    action_type VARCHAR(50) NOT NULL,
    budget_exceeded BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_user ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_project ON usage_logs(project_id);

-- =============================================================================
-- Functions
-- =============================================================================

-- Get next version number
CREATE OR REPLACE FUNCTION get_next_version_number(p_section_id UUID)
RETURNS INT AS $$
BEGIN
    RETURN COALESCE((SELECT MAX(version_number) + 1 FROM section_versions WHERE section_id = p_section_id), 1);
END;
$$ LANGUAGE plpgsql;

-- Check token budget
CREATE OR REPLACE FUNCTION check_token_budget(p_project_id UUID, p_requested_tokens INT DEFAULT 0)
RETURNS JSONB AS $$
DECLARE
    v_budget INT; v_used INT; v_threshold DECIMAL; v_remaining INT;
BEGIN
    SELECT max_token_budget, used_tokens, budget_alert_threshold INTO v_budget, v_used, v_threshold
    FROM projects WHERE id = p_project_id;
    IF NOT FOUND THEN RETURN jsonb_build_object('error', 'Project not found', 'allowed', FALSE); END IF;
    v_remaining := v_budget - v_used;
    RETURN jsonb_build_object(
        'allowed', (v_remaining >= p_requested_tokens),
        'remaining', v_remaining,
        'used', v_used,
        'budget', v_budget,
        'usage_percent', ROUND((v_used::DECIMAL / NULLIF(v_budget, 0)) * 100, 2)
    );
END;
$$ LANGUAGE plpgsql;

-- Update project tokens trigger
CREATE OR REPLACE FUNCTION update_project_tokens() RETURNS TRIGGER AS $$
BEGIN
    UPDATE projects SET used_tokens = used_tokens + NEW.total_tokens, updated_at = NOW() WHERE id = NEW.project_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_project_tokens ON usage_logs;
CREATE TRIGGER trg_update_project_tokens AFTER INSERT ON usage_logs
    FOR EACH ROW WHEN (NEW.project_id IS NOT NULL) EXECUTE FUNCTION update_project_tokens();

-- Auto update timestamp
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Seed Data
-- =============================================================================

-- Admin user (password: admin123)
INSERT INTO users (id, email, password_hash, full_name, role) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'admin@example.com', 
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.LwP2OVZwBHXJWO', 'System Admin', 'Admin')
ON CONFLICT (email) DO NOTHING;

-- Editor user (password: user123)
INSERT INTO users (id, email, password_hash, full_name, role) VALUES
    ('a0000000-0000-0000-0000-000000000002', 'editor@example.com',
     '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Test Editor', 'Editor')
ON CONFLICT (email) DO NOTHING;

-- Default AI Personas
INSERT INTO ai_personas (id, name, description, system_prompt, preferred_model, is_system) VALUES
    ('b0000000-0000-0000-0000-000000000001', '專業技術寫手', '擅長撰寫技術規格、系統架構等專業內容',
     '你是一位資深的技術文件撰寫專家，專門協助撰寫政府標案建議書中的技術章節。請使用正式、專業的語調，確保內容完整、邏輯清晰。回應時請使用繁體中文。', 'gpt-4o', TRUE),
    ('b0000000-0000-0000-0000-000000000002', '法規合規專家', '熟悉政府採購法規與合規要求',
     '你是一位政府採購法規專家，熟悉台灣政府採購法及相關規定。協助撰寫建議書時，請確保內容符合法規要求。回應時請使用繁體中文。', 'gpt-4o', TRUE),
    ('b0000000-0000-0000-0000-000000000003', '商業企劃專家', '擅長撰寫公司簡介、效益分析等商業內容',
     '你是一位經驗豐富的商業企劃專家，擅長撰寫公司介紹、專案實績、成本效益分析等內容。請使用具有說服力的語言。回應時請使用繁體中文。', 'gpt-4o', TRUE)
ON CONFLICT DO NOTHING;

SELECT 'Database initialization completed!' AS status;
