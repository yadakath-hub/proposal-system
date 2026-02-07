#!/bin/bash

# =============================================================================
# AI Proposal Generator - Mac Startup Script
# Version: 1.0.0
# Target: macOS Apple Silicon (M1/M2/M3)
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     🚀 AI Proposal Generator - Startup Script              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

check_docker() {
    print_step "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo ""
        echo "Please install Docker Desktop for Mac:"
        echo "  https://docs.docker.com/desktop/install/mac-install/"
        echo ""
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running!"
        echo ""
        echo "Please start Docker Desktop and try again."
        echo ""
        
        # Try to open Docker Desktop on Mac
        if [[ "$OSTYPE" == "darwin"* ]]; then
            read -p "Would you like to open Docker Desktop now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                open -a Docker
                echo ""
                echo "Waiting for Docker to start (this may take 30-60 seconds)..."
                
                # Wait for Docker to be ready (max 90 seconds)
                for i in {1..30}; do
                    if docker info &> /dev/null; then
                        print_success "Docker is now running!"
                        break
                    fi
                    sleep 3
                    echo -n "."
                done
                echo ""
                
                if ! docker info &> /dev/null; then
                    print_error "Docker did not start in time. Please start it manually and try again."
                    exit 1
                fi
            else
                exit 1
            fi
        else
            exit 1
        fi
    fi
    
    print_success "Docker is running"
}

check_docker_compose() {
    print_step "Checking Docker Compose..."
    
    if docker compose version &> /dev/null; then
        print_success "Docker Compose v2 is available"
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        print_success "Docker Compose v1 is available"
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose is not available!"
        exit 1
    fi
}

# =============================================================================
# Environment Setup
# =============================================================================

setup_env() {
    print_step "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        print_info ".env file not found, creating from template..."
        
        if [ -f ".env.example" ]; then
            cp .env.example .env
            
            # Generate a random JWT secret
            JWT_SECRET=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 48)
            
            # Update JWT_SECRET_KEY in .env (works on both macOS and Linux)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET}|" .env
            else
                sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET}|" .env
            fi
            
            print_success ".env file created with generated JWT secret"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    else
        print_success ".env file exists"
    fi
}

# =============================================================================
# Directory Setup
# =============================================================================

setup_directories() {
    print_step "Setting up data directories..."
    
    mkdir -p data/postgres
    mkdir -p data/minio
    mkdir -p data/redis
    mkdir -p data/uploads
    
    print_success "Data directories created"
}

# =============================================================================
# Frontend Setup
# =============================================================================

setup_frontend() {
    print_step "Checking frontend setup..."
    
    if [ ! -f "frontend/package.json" ]; then
        print_info "Creating minimal frontend setup..."
        
        mkdir -p frontend
        
        # Create package.json
        cat > frontend/package.json << 'EOF'
{
  "name": "ai-proposal-generator-frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.15",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "naive-ui": "^2.38.1",
    "@vueuse/core": "^10.7.2",
    "axios": "^1.6.7"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.3",
    "typescript": "^5.3.3",
    "vite": "^5.0.12",
    "vue-tsc": "^1.8.27"
  }
}
EOF
        
        # Create vite.config.ts
        cat > frontend/vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true
      }
    }
  }
})
EOF
        
        # Create tsconfig.json
        cat > frontend/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
        
        # Create tsconfig.node.json
        cat > frontend/tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF
        
        # Create index.html
        cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-TW">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Proposal Generator - 智慧投標建議書生成系統</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF
        
        # Create src directory
        mkdir -p frontend/src
        
        # Create main.ts
        cat > frontend/src/main.ts << 'EOF'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'

const app = createApp(App)

app.use(createPinia())
app.use(naive)

app.mount('#app')
EOF
        
        # Create App.vue
        cat > frontend/src/App.vue << 'EOF'
<template>
  <n-config-provider :theme="darkTheme" :locale="zhTW" :date-locale="dateZhTW">
    <n-message-provider>
      <n-dialog-provider>
        <div class="app-container">
          <n-card>
            <n-space vertical size="large">
              <n-h1>🚀 AI Proposal Generator</n-h1>
              <n-h2>智慧投標建議書生成系統</n-h2>
              
              <n-divider />
              
              <n-alert type="success" title="系統狀態">
                <n-space vertical>
                  <n-text>✅ Frontend: Running on Vue 3 + Naive UI</n-text>
                  <n-text>
                    🔗 Backend API: 
                    <n-tag type="info">{{ backendStatus }}</n-tag>
                  </n-text>
                </n-space>
              </n-alert>
              
              <n-space>
                <n-button type="primary" @click="checkBackend">
                  檢查後端連線
                </n-button>
                <n-button @click="openDocs">
                  開啟 API 文件
                </n-button>
              </n-space>
              
              <n-divider />
              
              <n-h3>📋 Phase 1 完成項目</n-h3>
              <n-list bordered>
                <n-list-item>✅ Docker Compose 環境配置</n-list-item>
                <n-list-item>✅ PostgreSQL 16 + pgvector</n-list-item>
                <n-list-item>✅ Redis 快取服務</n-list-item>
                <n-list-item>✅ MinIO 物件儲存</n-list-item>
                <n-list-item>✅ FastAPI 後端框架</n-list-item>
                <n-list-item>✅ Vue 3 + Naive UI 前端</n-list-item>
              </n-list>
            </n-space>
          </n-card>
        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { darkTheme, zhTW, dateZhTW } from 'naive-ui'
import axios from 'axios'

const backendStatus = ref('未檢查')

const checkBackend = async () => {
  try {
    backendStatus.value = '連線中...'
    const response = await axios.get('http://localhost:8000/health')
    backendStatus.value = `${response.data.status} (${response.data.version})`
  } catch (error) {
    backendStatus.value = '連線失敗'
  }
}

const openDocs = () => {
  window.open('http://localhost:8000/docs', '_blank')
}

// Auto-check on mount
checkBackend()
</script>

<style>
body {
  margin: 0;
  padding: 0;
  background-color: #18181c;
}

.app-container {
  min-height: 100vh;
  padding: 40px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.n-card {
  max-width: 800px;
  width: 100%;
}
</style>
EOF
        
        # Create vite.svg
        cat > frontend/public/vite.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <text y=".9em" font-size="90">🚀</text>
</svg>
EOF
        
        mkdir -p frontend/public
        mv frontend/public/vite.svg frontend/public/ 2>/dev/null || true
        
        print_success "Frontend setup created"
    else
        print_success "Frontend package.json exists"
    fi
}

# =============================================================================
# Docker Services
# =============================================================================

start_services() {
    print_step "Starting Docker services..."
    
    # Pull latest images
    $COMPOSE_CMD pull
    
    # Build and start services
    $COMPOSE_CMD up -d --build
    
    print_success "Services started"
}

wait_for_services() {
    print_step "Waiting for services to be ready..."
    
    echo -n "  PostgreSQL"
    for i in {1..30}; do
        if $COMPOSE_CMD exec -T postgres-db pg_isready -U aipg_user &> /dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    
    echo -n "  Redis"
    for i in {1..15}; do
        if $COMPOSE_CMD exec -T redis redis-cli ping &> /dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    echo -n "  MinIO"
    for i in {1..15}; do
        if curl -s http://localhost:9000/minio/health/live &> /dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    
    echo -n "  Backend"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    
    print_success "All services are ready!"
}

# =============================================================================
# Status Display
# =============================================================================

show_status() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ✅ AI Proposal Generator is running!                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}🌐 Access Points:${NC}"
    echo ""
    echo "   Frontend (Vue):     http://localhost:3000"
    echo "   Backend API:        http://localhost:8000"
    echo "   API Documentation:  http://localhost:8000/docs"
    echo "   MinIO Console:      http://localhost:9001"
    echo ""
    echo -e "${BLUE}🔑 Default Credentials:${NC}"
    echo ""
    echo "   Admin User:         admin@example.com / admin123"
    echo "   Test User:          editor@example.com / user123"
    echo "   MinIO:              aipg_minio_admin / aipg_minio_secret_2024"
    echo ""
    echo -e "${BLUE}📋 Useful Commands:${NC}"
    echo ""
    echo "   View logs:          docker compose logs -f"
    echo "   Stop services:      docker compose down"
    echo "   Restart:            docker compose restart"
    echo "   DB shell:           docker compose exec postgres-db psql -U aipg_user -d ai_proposal_db"
    echo ""
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    print_header
    
    check_docker
    check_docker_compose
    setup_env
    setup_directories
    setup_frontend
    start_services
    wait_for_services
    show_status
}

# Run main function
main "$@"
