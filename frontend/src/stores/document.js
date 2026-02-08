import { defineStore } from 'pinia'
import { ref } from 'vue'
import { documentApi } from '@/api/documents'

export const useDocumentStore = defineStore('document', () => {
  const documents = ref([])
  const loading = ref(false)

  async function fetchDocuments(projectId) {
    loading.value = true
    try {
      const response = await documentApi.getDocuments(projectId)
      documents.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function uploadDocument(projectId, file) {
    const response = await documentApi.upload(projectId, file)
    documents.value.unshift(response.data)
    return response.data
  }

  async function processDocument(documentId) {
    const response = await documentApi.processDocument(documentId)
    const index = documents.value.findIndex(d => d.id === documentId)
    if (index !== -1) {
      documents.value[index] = { ...documents.value[index], is_parsed: true, chunk_count: response.data.chunk_count }
    }
    return response.data
  }

  async function deleteDocument(documentId) {
    await documentApi.deleteDocument(documentId)
    documents.value = documents.value.filter(d => d.id !== documentId)
  }

  async function searchDocuments(query, projectId, topK = 5) {
    const response = await documentApi.search({ query, project_id: projectId, top_k: topK })
    return response.data
  }

  return {
    documents,
    loading,
    fetchDocuments,
    uploadDocument,
    processDocument,
    deleteDocument,
    searchDocuments
  }
})
