<template>
  <div class="p-6">
    <!-- Stats cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <el-card shadow="hover" v-for="stat in stats" :key="stat.label">
        <div class="flex items-center">
          <div class="p-3 rounded-full" :class="stat.bgColor">
            <el-icon :size="24" :class="stat.textColor">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="ml-4">
            <p class="text-2xl font-bold">{{ stat.value }}</p>
            <p class="text-gray-500 text-sm">{{ stat.label }}</p>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Recent projects -->
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold">最近專案</h2>
      <el-button type="primary" :icon="Plus" @click="goToProjects">
        查看全部
      </el-button>
    </div>

    <div v-loading="loading" class="grid grid-cols-1 md:grid-cols-3 gap-6">
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
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-600'
  },
  {
    label: '進行中',
    value: projectStore.projects.filter(p => p.status === 'InProgress').length,
    icon: Clock,
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-600'
  },
  {
    label: '已完成',
    value: projectStore.projects.filter(p => p.status === 'Completed').length,
    icon: CircleCheckFilled,
    bgColor: 'bg-green-100',
    textColor: 'text-green-600'
  },
  {
    label: '草稿',
    value: projectStore.projects.filter(p => p.status === 'Draft').length,
    icon: Document,
    bgColor: 'bg-purple-100',
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
