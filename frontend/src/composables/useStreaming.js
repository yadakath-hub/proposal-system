import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function useStreaming() {
  const content = ref('')
  const isStreaming = ref(false)
  const error = ref(null)
  const tokenCount = ref({ input: 0, output: 0 })

  let abortController = null

  async function startStream(url, body) {
    const authStore = useAuthStore()

    content.value = ''
    error.value = null
    isStreaming.value = true
    tokenCount.value = { input: 0, output: 0 }

    abortController = new AbortController()

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify(body),
        signal: abortController.signal
      })

      if (!response.ok) {
        let msg = '生成失敗'
        try {
          const errorData = await response.json()
          msg = errorData.detail || msg
        } catch {}
        throw new Error(msg)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        // Keep last potentially incomplete part in buffer
        buffer = parts.pop() || ''

        for (const part of parts) {
          processSSEEvent(part)
        }
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        processSSEEvent(buffer)
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        // User cancelled
      } else {
        error.value = e.message
      }
    } finally {
      isStreaming.value = false
      abortController = null
    }
  }

  function processSSEEvent(raw) {
    let eventType = 'message'
    let data = ''

    for (const line of raw.split('\n')) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        data = line.slice(6)
      }
    }

    if (!data) return

    try {
      const parsed = JSON.parse(data)

      if (eventType === 'message' && parsed.content) {
        content.value += parsed.content
      } else if (eventType === 'done') {
        isStreaming.value = false
      } else if (eventType === 'error') {
        error.value = parsed.error || '生成過程中發生錯誤'
        isStreaming.value = false
      }
    } catch {
      // Non-JSON data line, treat as content
      if (data.trim() && data !== '[DONE]') {
        content.value += data
      }
    }
  }

  function stopStream() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isStreaming.value = false
  }

  function clearContent() {
    content.value = ''
    error.value = null
    tokenCount.value = { input: 0, output: 0 }
  }

  return {
    content,
    isStreaming,
    error,
    tokenCount,
    startStream,
    stopStream,
    clearContent
  }
}
