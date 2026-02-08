<template>
  <div class="page-container">
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">儀表板</h1>
        <p class="page-subtitle">專案總覽與快速操作</p>
      </div>
    </div>

    <!-- Stats cards -->
    <div class="stats-grid">
      <el-card shadow="hover" v-for="stat in stats" :key="stat.label" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" :class="stat.bgColor">
            <el-icon :size="24" :class="stat.textColor">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-value">{{ stat.value }}</p>
            <p class="stat-label">{{ stat.label }}</p>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Recent projects -->
    <div class="section-header">
      <h2 class="section-title">最近專案</h2>
      <el-button type="primary" :icon="Plus" @click="goToProjects">
        查看全部
      </el-button>
    </div>

    <div v-loading="loading" class="projects-grid">
      <ProjectCard
        v-for="project in recentProjects"
        :key="project.id"
        :project="project"
        @click="goToProject(project.id)"
      />

      <el-empty v-if="!loading && recentProjects.length === 0" description="尚無專案" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import ProjectCard from '@/components/project/ProjectCard.vue'
import { Folder, Document, Clock, CircleCheckFilled, Plus } from '@element-plus/icons-vue'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)

const recentProjects = computed(() => projectStore.projects.slice(0, 6))

const stats = computed(() => [
  {
    label: '總專案數',
    value: projectStore.projectCount,
    icon: Folder,
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600'
  },
  {
    label: '進行中',
    value: projectStore.projects.filter(p => p.status === 'InProgress').length,
    icon: Clock,
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-600'
  },
  {
    label: '已完成',
    value: projectStore.projects.filter(p => p.status === 'Completed').length,
    icon: CircleCheckFilled,
    bgColor: 'bg-green-50',
    textColor: 'text-green-600'
  },
  {
    label: '草稿',
    value: projectStore.projects.filter(p => p.status === 'Draft').length,
    icon: Document,
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-600'
  }
])

onMounted(async () => {
  loading.value = true
  try {
    await projectStore.fetchProjects()
  } finally {
    loading.value = false
  }
})

function goToProjects() {
  router.push('/projects')
}

function goToProject(id) {
  router.push(`/projects/${id}`)
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 4px 0 0;
}

.stats-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, 1fr);
  margin-bottom: 32px;
}

@media (min-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat-card {
  border: 1px solid var(--border-color);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 2px 0 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.projects-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

@media (min-width: 1536px) {
  .projects-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
