import { defineStore } from 'pinia'
import { ref } from 'vue'
import { conversationAPI } from '../api'

export interface Message {
  id?: string
  role: 'user' | 'assistant'
  content: string
  sources: Array<{
    filename: string
    snippet: string
    page?: number
    chunk_index?: number
  }>
}

export interface Conversation {
  id: string
  title: string
  updated_at: string
  message_count: number
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)

  async function loadConversations() {
    try {
      const res = await conversationAPI.list()
      conversations.value = res.data
    } catch (e) {
      console.error('加载会话列表失败', e)
    }
  }

  async function createConversation(title?: string) {
    const res = await conversationAPI.create({ title })
    const conv = res.data
    conversations.value.unshift(conv)
    return conv
  }

  async function deleteConversation(id: string) {
    await conversationAPI.delete(id)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (currentConversationId.value === id) {
      currentConversationId.value = null
      messages.value = []
    }
  }

  async function loadMessages(convId: string) {
    try {
      const res = await conversationAPI.getMessages(convId)
      messages.value = res.data.map((m: any) => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        sources: m.sources || [],
      }))
    } catch (e) {
      console.error('加载消息失败', e)
      messages.value = []
    }
  }

  function addUserMessage(content: string) {
    messages.value.push({
      role: 'user',
      content,
      sources: [],
    })
  }

  function addAssistantToken(token: string) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content += token
    }
  }

  function startAssistantMessage() {
    messages.value.push({
      role: 'assistant',
      content: '',
      sources: [],
    })
  }

  function setAssistantSources(sources: any[]) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.sources = sources
    }
  }

  function setStreaming(val: boolean) {
    isStreaming.value = val
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    conversations,
    currentConversationId,
    messages,
    isStreaming,
    loadConversations,
    createConversation,
    deleteConversation,
    loadMessages,
    addUserMessage,
    addAssistantToken,
    startAssistantMessage,
    setAssistantSources,
    setStreaming,
    clearMessages,
  }
})
