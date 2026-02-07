# 📋 AI Proposal Generator - 專案進度追蹤文件

> **最後更新**: 2025-02-07
> **當前階段**: Phase 1 - Environment Setup ✅ 完成

---

## 🎯 專案概述

**專案名稱**: 智慧投標建議書生成系統 (AI Proposal Generator)  
**目標**: 協助業務團隊撰寫 200 頁政府標案建議書，整合 AI 自動撰寫功能  
**部署方式**: Docker Compose on localhost (macOS Apple Silicon)

---

## 📊 完成進度

| 階段 | 狀態 | 說明 |
|------|------|------|
| 1. 架構設計 | ✅ v2.0 | 三層式架構、DB Schema (含版本控制+RAG)、API 規劃 |
| 2. 環境建置 | ✅ 完成 | Docker Compose、PostgreSQL+pgvector、Redis、MinIO |
| 3. 後端基礎 | ✅ 完成 | FastAPI 專案結構、Config、Health Check |
| 4. 認證模組 | 🔜 下一步 | JWT + RBAC |
| 5. 專案管理 | ⏳ 待開始 | CRUD + 章節樹 |
| 6. AI 整合 | ⏳ 待開始 | LangChain + OpenAI/Gemini |
| 7. 檔案處理 | ⏳ 待開始 | PDF 解析 + 上傳 |
| 8. 匯出功能 | ⏳ 待開始 | Word/PDF 生成 |
| 9. 前端開發 | ⏳ 待開始 | Vue 3 + Naive UI |
| 10. 整合測試 | ⏳ 待開始 | E2E Testing |

---

## 🗂️ 檔案結構 (Phase 1 完成)

```
ai-proposal-generator/
├── docker-compose.yml          # ✅ Docker 服務編排
├── start_mac.sh               # ✅ Mac 一鍵啟動腳本
├── .env.example               # ✅ 環境變數範例
├── .gitignore                 # ✅ Git 忽略規則
├── README.md                  # ✅ 專案說明文件
├── project_status.md          # ✅ 本文件
│
├── backend/
│   ├── Dockerfile             # ✅ FastAPI 容器配置
│   ├── requirements.txt       # ✅ Python 依賴套件
│   ├── init_db.sql           # ✅ 資料庫初始化腳本 (含所有 Tables)
│   └── app/
│       ├── __init__.py       # ✅
│       ├── main.py           # ✅ FastAPI 入口
│       ├── core/
│       │   ├── __init__.py   # ✅
│       │   └── config.py     # ✅ Pydantic Settings
│       ├── api/              # ⏳ 待實作
│       ├── db/               # ⏳ 待實作
│       ├── models/           # ⏳ 待實作
│       ├── schemas/          # ⏳ 待實作
│       └── services/         # ⏳ 待實作
│
├── frontend/                  # ✅ 基礎結構 (由 start_mac.sh 生成)
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.ts
│       └── App.vue
│
└── data/                      # ✅ 持久化資料目錄 (Git 忽略)
    ├── postgres/
    ├── redis/
    └── minio/
```

---

## 🐳 Docker Services (Phase 1)

| Service | Container | Port | 說明 |
|---------|-----------|------|------|
| PostgreSQL | aipg-postgres | 5432 | 主資料庫 (含 pgvector) |
| Redis | aipg-redis | 6379 | 快取與訊息佇列 |
| MinIO | aipg-minio | 9000/9001 | S3 相容物件儲存 |
| Backend | aipg-backend | 8000 | FastAPI 後端 |
| Frontend | aipg-frontend | 3000 | Vue 3 開發伺服器 |

### 訪問端點
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

### 預設帳號
| 服務 | 帳號 | 密碼 |
|------|------|------|
| Admin User | admin@example.com | admin123 |
| Editor User | editor@example.com | user123 |
| MinIO | aipg_minio_admin | aipg_minio_secret_2024 |

---

## 🗄️ 資料庫 Schema (v2.0 - 2025-02-05 更新)

> **重大更新**: 
> - ✅ 版本控制重構為一對多關聯
> - ✅ 新增 pgvector 向量支援
> - ✅ 新增 Word 範本標籤對應
> - ✅ 新增專案 Token 預算控制

### PostgreSQL Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- UUID 生成
CREATE EXTENSION IF NOT EXISTS "pgvector";    -- 🆕 向量相似度搜尋
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- 模糊文字搜尋
```

### Tables 清單

| Table | 用途 | 主要欄位 | 備註 |
|-------|------|----------|------|
| `users` | 使用者帳號 | id, email, password_hash, role, full_name | |
| `projects` | 標案專案 | id, name, tender_pdf_path, deadline, status, **max_token_budget**, **used_tokens** | 🆕 預算控制 |
| `project_members` | 專案成員 | id, project_id, user_id, project_role | |
| `sections` | 章節樹 | id, project_id, parent_id, chapter_number, title, **docx_template_tag**, **current_version_id**, **locked_by** | 🆕 原 project_structure，重新命名 |
| `section_versions` | 章節版本 | id, section_id, **version_number**, content, **source_type**, created_by | 🆕 取代扁平欄位設計 |
| `templates` | Word/PDF 範本 | id, name, template_type, file_path, style_config, **tag_schema** | 🆕 標籤結構定義 |
| `project_templates` | 專案-範本關聯 | id, project_id, template_id, usage_type | 🆕 多對多關聯 |
| `document_embeddings` | 向量嵌入 | id, source_type, source_id, chunk_text, **embedding vector(1536)** | 🆕 RAG 支援 |
| `ai_personas` | AI 人設 | id, name, system_prompt, preferred_model, parameters | |
| `usage_logs` | Token 使用紀錄 | id, user_id, project_id, **section_id**, **version_id**, model_used, total_tokens, cost_usd | 🆕 關聯到版本 |

### ENUM 類型

```sql
-- 全域角色
CREATE TYPE user_role AS ENUM ('Admin', 'Editor', 'Reviewer', 'Viewer');

-- 專案角色
CREATE TYPE project_role AS ENUM ('Owner', 'Manager', 'Writer', 'Reviewer');

-- 專案狀態
CREATE TYPE project_status AS ENUM ('Draft', 'InProgress', 'Review', 'Completed');

-- 章節狀態
CREATE TYPE section_status AS ENUM ('NotStarted', 'Writing', 'Review', 'Approved');

-- 🆕 版本來源類型 (取代 selected_version)
CREATE TYPE version_source AS ENUM (
    'Human',           -- 人工撰寫
    'GPT4',            -- gpt-4
    'GPT4o',           -- gpt-4o
    'GPT4oMini',       -- gpt-4o-mini
    'Gemini15Pro',     -- gemini-1.5-pro
    'Gemini15Flash',   -- gemini-1.5-flash
    'Gemini20Flash',   -- gemini-2.0-flash
    'Imported'         -- 從範本/歷史匯入
);

-- 🆕 嵌入來源類型
CREATE TYPE embedding_source AS ENUM (
    'Template',            -- 來自範本
    'HistoricalProposal',  -- 歷史得標建議書
    'TenderDocument',      -- 招標文件
    'Section'              -- 已撰寫章節
);

-- 範本類型
CREATE TYPE template_type AS ENUM ('CoverPage', 'TOC', 'Chapter', 'Appendix', 'FullDoc');

-- 🆕 範本用途
CREATE TYPE template_usage AS ENUM ('Main', 'Reference');
```

### 核心 Table Schema

#### `sections` (章節樹 - 支援併發鎖定)
```sql
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    chapter_number VARCHAR(20) NOT NULL,      -- "1.2.3" 格式
    title VARCHAR(500) NOT NULL,
    requirement_text TEXT,                     -- 原始招標需求
    sort_order INT NOT NULL DEFAULT 0,
    depth_level INT NOT NULL DEFAULT 0,
    assigned_to UUID REFERENCES users(id),
    estimated_pages INT DEFAULT 1,
    status section_status DEFAULT 'NotStarted',
    docx_template_tag VARCHAR(100),            -- 🆕 對應 {{ section_1_2_3 }}
    current_version_id UUID,                   -- 🆕 當前選定版本
    locked_by UUID REFERENCES users(id),       -- 🆕 編輯鎖定者
    locked_at TIMESTAMP WITH TIME ZONE,
    lock_expires_at TIMESTAMP WITH TIME ZONE,  -- 🆕 鎖定 5 分鐘後自動過期
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, chapter_number)
);
```

#### `section_versions` (版本控制)
```sql
CREATE TABLE section_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content TEXT NOT NULL,
    content_html TEXT,
    source_type version_source NOT NULL,       -- 🆕 Human/GPT4o/Gemini 等
    created_by UUID NOT NULL REFERENCES users(id),
    persona_id UUID REFERENCES ai_personas(id),
    metadata JSONB DEFAULT '{}'::jsonb,        -- {"word_count": 500, "tokens": 650}
    is_final BOOLEAN DEFAULT FALSE,
    prompt_used TEXT,                          -- 記錄使用的 prompt
    generation_params JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(section_id, version_number)
);
```

#### `document_embeddings` (RAG 向量表)
```sql
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type embedding_source NOT NULL,
    source_id UUID NOT NULL,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,           -- 🆕 OpenAI text-embedding-3-small
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_type, source_id, chunk_index)
);

-- IVFFlat 索引 (向量相似度搜尋)
CREATE INDEX idx_embeddings_vector 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 關鍵 Database Functions

```sql
-- 取得下一個版本號
CREATE FUNCTION get_next_version_number(p_section_id UUID) RETURNS INT;

-- 檢查 Token 預算
CREATE FUNCTION check_token_budget(p_project_id UUID, p_requested_tokens INT) RETURNS JSONB;
-- 回傳: {"allowed": true, "remaining": 50000, "warning": false, "usage_percent": 50.00}
```

---

## 🔌 API 模組 (設計完成)

| 模組 | Base Path | Endpoints 數量 | 說明 |
|------|-----------|----------------|------|
| Auth | `/api/v1/auth` | 5 | 登入/註冊/Token |
| Users | `/api/v1/users` | 5 | 使用者管理 |
| Projects | `/api/v1/projects` | 12 | 專案+章節管理 |
| Sections | `/api/v1/sections` | 4 | 內容編輯 |
| AI | `/api/v1/ai` | 8 | AI 生成/人設 |
| Files | `/api/v1/files` | 5 | 檔案上傳 |
| Export | `/api/v1/export` | 4 | Word/PDF 匯出 |
| Analytics | `/api/v1/analytics` | 4 | 使用量統計 |

---

## 🛠️ 技術棧 (v2.0 - 2025-02-05 更新)

### Database & Storage
| 技術 | 版本 | 用途 |
|------|------|------|
| PostgreSQL | 16+ | 主資料庫 |
| pgvector | 0.6+ | 🆕 向量相似度搜尋 (RAG) |
| pg_trgm | 內建 | 模糊文字搜尋 |
| SQLAlchemy | 2.0+ | ORM (async 支援) |
| Alembic | 1.13+ | DB Migration |
| asyncpg | 0.29+ | Async PostgreSQL Driver |
| MinIO | latest | S3 相容檔案儲存 |
| Redis | 7+ | 快取/分散式鎖 (可選) |

### Backend (Python)
| 技術 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.109+ | Web Framework |
| Pydantic | 2.x | 資料驗證 |
| python-jose | 3.3+ | JWT 認證 |
| bcrypt | 4.1+ | 密碼雜湊 |
| httpx | 0.26+ | Async HTTP Client |
| sse-starlette | 1.8+ | Server-Sent Events |

### AI Engine
| 技術 | 版本 | 用途 |
|------|------|------|
| LangChain | 0.1+ | LLM 整合框架 |
| OpenAI SDK | 1.10+ | GPT-4o / GPT-4o-mini |
| Google GenAI | 0.3+ | Gemini 1.5/2.0 |
| tiktoken | 0.5+ | Token 計算 |

### 🆕 Embedding & RAG
| 技術 | 模型/規格 | 用途 |
|------|----------|------|
| OpenAI Embedding | text-embedding-3-small | 向量生成 (1536 維) |
| pgvector | IVFFlat Index | 向量相似度搜尋 |
| LangChain | RecursiveCharacterTextSplitter | 文件分塊 |

### File Processing
| 技術 | 版本 | 用途 |
|------|------|------|
| PyMuPDF (fitz) | 1.23+ | PDF 解析/提取 |
| python-docx | 1.1+ | Word 讀取/基礎生成 |
| docxtpl | 0.16+ | 🆕 Word Jinja2 範本引擎 |
| WeasyPrint | 60+ | HTML to PDF |
| pytesseract | 0.3+ | OCR (可選) |

### Frontend (Vue)
| 技術 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | Framework (Composition API) |
| Vite | 5.x | Build Tool |
| Pinia | 2.1+ | 狀態管理 |
| Naive UI | 2.38+ | 企業級 UI 元件 |
| Vue Router | 4.2+ | 路由 |
| TypeScript | 5.3+ | 型別安全 |
| @vueuse/core | 10+ | 工具函數 |
| Tiptap | 2.2+ | 🆕 富文本編輯器 |
| diff-match-patch | 1.0+ | 🆕 版本差異比對 |

### Infrastructure
| 技術 | 用途 |
|------|------|
| Docker | 容器化 |
| Docker Compose | 開發環境編排 |
| Nginx | 反向代理 (生產) |

---

## 📝 待辦事項

### 下一步 (Phase 2: 資料庫建置)
- [ ] 建立 PostgreSQL Docker 環境
- [ ] 撰寫 SQLAlchemy Models
- [ ] 建立 Alembic Migration
- [ ] 建立種子資料 (Seed Data)

---

## 🔧 環境變數規劃

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_proposal

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# File Storage
STORAGE_TYPE=local  # or 's3', 'minio'
STORAGE_PATH=/data/uploads
S3_BUCKET=ai-proposal-files
S3_ENDPOINT=...

# App
APP_ENV=development
DEBUG=true
```

---

## 📌 設計決策記錄

### 2025-02-05: 初始架構設計 (v1.0)
- **決策**: 採用三層式架構 (Presentation + Application + Data)
- **理由**: 企業級系統需要清晰的關注點分離，便於團隊協作與維護
- **備選方案**: 微服務架構 (暫不採用，MVP 階段保持簡單)

### 2025-02-05: 架構改進 (v2.0) 🆕

#### 決策 1: 版本控制重構
- **原設計**: `section_content` 表包含 4 個扁平欄位 (user_draft, ai_v1, ai_v2, final)
- **新設計**: 獨立 `section_versions` 表，一對多關聯
- **理由**: 
  - 支援無限版本數量
  - 可追蹤每個版本的來源 (Human/GPT4o/Gemini 等)
  - 便於實作版本比對功能
- **新增欄位**: `source_type` ENUM、`version_number`、`prompt_used`

#### 決策 2: 併發編輯控制
- **決策**: `sections` 表新增 `locked_by`、`locked_at`、`lock_expires_at`
- **理由**: 多人協作時避免編輯衝突，採用悲觀鎖策略
- **鎖定策略**: 5 分鐘自動過期，避免死鎖

#### 決策 3: 向量搜尋支援 (RAG)
- **決策**: 使用 pgvector 擴展 + `document_embeddings` 表
- **理由**: 實現智慧範本推薦、歷史標案參考功能
- **技術規格**: 
  - Embedding Model: OpenAI text-embedding-3-small (1536 維)
  - Index: IVFFlat (lists=100)
  - Similarity: Cosine

#### 決策 4: Word 範本動態對應
- **決策**: `sections` 表新增 `docx_template_tag` 欄位
- **理由**: 配合 docxtpl 的 Jinja2 語法，實現動態內容填充
- **範例**: `docx_template_tag = "section_1_2_3"` 對應 Word 中的 `{{ section_1_2_3 }}`

#### 決策 5: Token 預算控制
- **決策**: `projects` 表新增 `max_token_budget`、`used_tokens`
- **理由**: 
  - 防止 AI API 費用失控
  - 支援專案級別的成本管理
- **實作**: `check_token_budget()` 函數在每次 AI 呼叫前檢查

### 2025-02-05: RBAC 雙層設計
- **決策**: 全域角色 (Admin/Editor/Reviewer/Viewer) + 專案角色 (Owner/Manager/Writer/Reviewer)
- **理由**: 同一使用者在不同專案可能有不同權限
- **備選方案**: 單一角色系統 (不夠彈性)

---

*此文件會在每次開發對話後更新*
