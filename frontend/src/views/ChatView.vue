<template>
  <div class="chat-layout">
    <!-- 顶部导航 -->
    <header class="chat-header">
      <div class="header-left">
        <el-button
          text
          class="sidebar-toggle"
          @click="sidebarOpen = !sidebarOpen"
          :title="sidebarOpen ? '收起侧边栏' : '展开侧边栏'"
        >
          <el-icon :size="20"><Fold v-if="sidebarOpen" /><Expand v-else /></el-icon>
        </el-button>
        <h2>🤖 RAG 知识库问答</h2>
      </div>
      <div class="header-right">
        <el-tag v-if="authStore.isAdmin" type="danger" size="small">管理员</el-tag>
        <span class="user-name">{{ authStore.user?.username }}</span>
        <el-button v-if="authStore.isAdmin" type="primary" size="small" @click="$router.push('/admin')">
          知识库管理
        </el-button>
        <el-button size="small" @click="$router.push('/profile')">个人中心</el-button>
        <el-button size="small" type="danger" plain @click="handleLogout">退出</el-button>
      </div>
    </header>

    <!-- 主体区域 -->
    <div class="chat-body">
      <!-- 遮罩层（移动端点击关闭侧边栏） -->
      <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false" />

      <!-- 左侧会话列表 -->
      <aside :class="['chat-sidebar', { open: sidebarOpen }]">
        <div class="sidebar-header">
          <el-button type="primary" @click="handleNewChat" :disabled="chatStore.isStreaming" style="width: 100%">
            <el-icon :size="16"><Plus /></el-icon>
            <span>新会话</span>
          </el-button>
        </div>

        <!-- 会话搜索 -->
        <div class="sidebar-search" v-if="chatStore.conversations.length > 0">
          <el-input
            v-model="convSearch"
            placeholder="搜索会话..."
            size="small"
            clearable
            :prefix-icon="Search"
          />
        </div>

        <div class="conversation-list">
          <div
            v-for="conv in filteredConversations"
            :key="conv.id"
            :class="['conv-item', { active: chatStore.currentConversationId === conv.id }]"
            @click="selectConversation(conv.id)"
            @mouseenter="hoveringConvId = conv.id"
            @mouseleave="hoveringConvId = null"
          >
            <div class="conv-main">
              <div class="conv-title" v-if="editingConvId !== conv.id">
                {{ conv.title }}
              </div>
              <el-input
                v-else
                v-model="editingConvTitle"
                size="small"
                @blur="confirmRename(conv.id)"
                @keydown.enter="confirmRename(conv.id)"
                @keydown.escape="cancelRename"
                @click.stop
                ref="renameInputRef"
              />
              <div class="conv-meta">
                <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
                <span class="conv-actions" v-show="chatStore.currentConversationId === conv.id || hoveringConvId === conv.id">
                  <el-button
                    text
                    size="small"
                    @click.stop="startRename(conv, $event)"
                    title="重命名"
                  >
                    <el-icon :size="14"><Edit /></el-icon>
                  </el-button>
                  <el-popconfirm title="确认删除此会话？" @confirm="handleDeleteConv(conv.id, $event)">
                    <template #reference>
                      <el-button text size="small" type="danger" title="删除" @click.stop>
                        <el-icon :size="14"><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-popconfirm>
                </span>
              </div>
            </div>
          </div>
          <div v-if="filteredConversations.length === 0 && chatStore.conversations.length > 0" class="conv-empty">
            未找到匹配的会话
          </div>
          <div v-if="chatStore.conversations.length === 0" class="conv-empty">
            暂无会话，点击上方按钮创建
          </div>
        </div>
      </aside>

      <!-- 右侧对话区 -->
      <main class="chat-main">
        <!-- 空状态：欢迎页 -->
        <div v-if="!chatStore.currentConversationId" class="welcome-area">
          <div class="welcome-icon">🤖</div>
          <h1 class="welcome-title">RAG 知识库问答系统</h1>
          <p class="welcome-desc">基于 LangChain + 阿里云百炼的智能问答助手</p>

          <!-- 快速入口卡片 -->
          <div class="quick-actions">
            <div class="quick-card" @click="handleQuickStart">
              <span class="quick-icon">💬</span>
              <span class="quick-label">开始新对话</span>
              <span class="quick-hint">向知识库提问</span>
            </div>
            <div class="quick-card" v-if="authStore.isAdmin" @click="$router.push('/admin')">
              <span class="quick-icon">📂</span>
              <span class="quick-label">管理知识库</span>
              <span class="quick-hint">上传/管理文档</span>
            </div>
            <div class="quick-card" @click="$router.push('/profile')">
              <span class="quick-icon">👤</span>
              <span class="quick-label">个人中心</span>
              <span class="quick-hint">查看/修改账户信息</span>
            </div>
          </div>

          <!-- 示例问题 -->
          <div class="example-questions">
            <h3>💡 试试这些问题</h3>
            <div class="example-list">
              <div
                v-for="q in exampleQuestions"
                :key="q"
                class="example-item"
                @click="handleQuickAsk(q)"
              >
                {{ q }}
              </div>
            </div>
          </div>
        </div>

        <!-- 对话视图 -->
        <template v-else>
          <!-- 消息列表 -->
          <div class="message-area" ref="messageAreaRef">
            <div v-for="(msg, idx) in chatStore.messages" :key="idx" :class="['message', msg.role]">
              <div class="message-avatar">
                {{ msg.role === 'user' ? '👤' : '🤖' }}
              </div>
              <div class="message-body">
                <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
                <!-- 引用来源 -->
                <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
                  <el-divider content-position="left">📎 参考来源</el-divider>
                  <div v-for="(src, si) in msg.sources" :key="si" class="source-item">
                    <div class="source-header">
                      <el-tag size="small" type="info">[{{ si + 1 }}]</el-tag>
                      <span class="source-filename">{{ src.filename }}</span>
                      <span v-if="src.page" class="source-page">第 {{ src.page }} 页</span>
                    </div>
                    <div class="source-snippet">{{ src.snippet }}</div>
                  </div>
                </div>
                <!-- 操作按钮 -->
                <div v-if="msg.role === 'assistant' && msg.content" class="message-actions">
                  <el-button text size="small" @click="copyMessage(msg.content)">
                    <el-icon :size="14"><DocumentCopy /></el-icon>
                    {{ copiedMsgIdx === idx ? '已复制' : '复制' }}
                  </el-button>
                </div>
              </div>
            </div>
            <!-- 流式输出中的光标 -->
            <span v-if="chatStore.isStreaming" class="streaming-cursor">|</span>
            <div ref="messageBottomRef" />
          </div>
        </template>

        <!-- 底部输入区 -->
        <div class="input-area" v-if="chatStore.currentConversationId">
          <div class="input-row">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="inputRows"
              placeholder="输入你的问题，例如：这款羽绒服的填充物是什么？"
              :disabled="chatStore.isStreaming"
              @keydown.enter.exact="handleSend"
              @keydown.shift.enter="handleShiftEnter"
              @input="autoResizeInput"
              resize="none"
              class="chat-input"
            />
            <el-button
              v-if="!chatStore.isStreaming"
              type="primary"
              :disabled="!inputText.trim()"
              @click="handleSend"
              class="send-btn"
            >
              <el-icon :size="18"><Promotion /></el-icon>
            </el-button>
            <el-button
              v-else
              type="danger"
              @click="handleStopGeneration"
              class="send-btn"
            >
              停止
            </el-button>
          </div>
          <div class="input-hint">
            Enter 发送 · Shift+Enter 换行
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Delete, Edit, Fold, Expand, Plus, Search,
  Promotion, DocumentCopy,
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import { conversationAPI } from '../api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

// 侧边栏
const sidebarOpen = ref(true)
const hoveringConvId = ref<string | null>(null)

// 会话搜索
const convSearch = ref('')

// 重命名
const editingConvId = ref<string | null>(null)
const editingConvTitle = ref('')
const renameInputRef = ref()

// 输入
const inputText = ref('')
const inputRows = ref(3)
const messageAreaRef = ref<HTMLElement>()
const messageBottomRef = ref<HTMLElement>()

// 复制
const copiedMsgIdx = ref<number | null>(null)

// 取消流式请求
let abortController: AbortController | null = null

// Markdown 渲染器
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

// 示例问题
const exampleQuestions = [
  '这款产品的退换货政策是什么？',
  '羽绒服的填充物成分是什么？',
  '如何查询物流信息？',
  '商品支持哪些支付方式？',
]

// 过滤会话
const filteredConversations = computed(() => {
  if (!convSearch.value) return chatStore.conversations
  const keyword = convSearch.value.toLowerCase()
  return chatStore.conversations.filter(c => c.title.toLowerCase().includes(keyword))
})

onMounted(async () => {
  await chatStore.loadConversations()
  const convId = route.params.id as string
  if (convId && chatStore.conversations.find(c => c.id === convId)) {
    await selectConversation(convId)
  }
})

// 响应式：小屏默认收起侧边栏
function handleResize() {
  if (window.innerWidth < 768) sidebarOpen.value = false
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

// 选择会话
async function selectConversation(id: string) {
  chatStore.currentConversationId = id
  router.replace(`/chat/${id}`)
  await chatStore.loadMessages(id)
  await scrollToBottom()
}

// 新建会话
async function handleNewChat() {
  const conv = await chatStore.createConversation()
  await selectConversation(conv.id)
  sidebarOpen.value = window.innerWidth >= 768
  convSearch.value = ''
}

// 删除会话
async function handleDeleteConv(id: string, event?: any) {
  if (event?.stopPropagation) event.stopPropagation()
  await chatStore.deleteConversation(id)
  ElMessage.success('会话已删除')
  if (chatStore.currentConversationId === id) {
    chatStore.currentConversationId = null
    router.replace('/chat')
  }
}

// 重命名
function startRename(conv: any, event: MouseEvent) {
  event.stopPropagation()
  editingConvId.value = conv.id
  editingConvTitle.value = conv.title
  nextTick(() => {
    const el = document.querySelector('.conv-item .el-input__inner') as HTMLInputElement
    if (el) el.select()
  })
}

async function confirmRename(id: string) {
  const title = editingConvTitle.value.trim()
  if (title) {
    try {
      await conversationAPI.update(id, { title })
      const conv = chatStore.conversations.find(c => c.id === id)
      if (conv) conv.title = title
      ElMessage.success('已重命名')
    } catch {
      ElMessage.error('重命名失败')
    }
  }
  editingConvId.value = null
}

function cancelRename() {
  editingConvId.value = null
}

// 发送消息
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.isStreaming) return

  if (!chatStore.currentConversationId) {
    const conv = await chatStore.createConversation(text.slice(0, 20))
    chatStore.currentConversationId = conv.id
    router.replace(`/chat/${conv.id}`)
  }

  chatStore.addUserMessage(text)
  inputText.value = ''
  inputRows.value = 3
  chatStore.setStreaming(true)
  await scrollToBottom()

  abortController = new AbortController()

  try {
    const token = localStorage.getItem('token')
    const convId = chatStore.currentConversationId

    const response = await fetch(`/api/conversations/${convId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message: text }),
      signal: abortController.signal,
    })

    if (!response.ok) throw new Error('请求失败')

    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应流')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'sources') {
              chatStore.setAssistantSources(data.sources)
            } else if (data.type === 'token') {
              if (chatStore.messages.length === 0 || chatStore.messages[chatStore.messages.length - 1].role !== 'assistant') {
                chatStore.startAssistantMessage()
              }
              chatStore.addAssistantToken(data.content)
              await scrollToBottom()
            } else if (data.type === 'error') {
              ElMessage.error(data.content)
            }
          } catch {}
        }
      }
    }
  } catch (e: any) {
    if (e.name === 'AbortError') {
      // 用户主动停止
    } else {
      ElMessage.error('问答请求失败: ' + (e.message || '网络错误'))
    }
  } finally {
    chatStore.setStreaming(false)
    abortController = null
    await chatStore.loadConversations()
    await scrollToBottom()
  }
}

// Shift+Enter 换行
function handleShiftEnter() {
  inputText.value += '\n'
  autoResizeInput()
}

// 停止生成
function handleStopGeneration() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}

// 快速开始
function handleQuickStart() {
  if (!chatStore.currentConversationId) {
    handleNewChat()
  }
}

// 快速提问
async function handleQuickAsk(question: string) {
  if (!chatStore.currentConversationId) {
    await handleNewChat()
  }
  inputText.value = question
  await handleSend()
}

// Markdown 渲染
function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    return md.render(text)
  } catch {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/\n/g, '<br>')
  }
}

// 复制消息
async function copyMessage(content: string) {
  try {
    await navigator.clipboard.writeText(content)
    const idx = chatStore.messages.findIndex(m => m.content === content && m.role === 'assistant')
    copiedMsgIdx.value = idx
    setTimeout(() => { copiedMsgIdx.value = null }, 2000)
  } catch {
    ElMessage.error('复制失败')
  }
}

// 自动调整输入框行数
function autoResizeInput() {
  const lines = inputText.value.split('\n').length
  inputRows.value = Math.min(Math.max(lines, 3), 8)
}

// 格式化时间
function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN')
}

// 平滑滚动到底部
async function scrollToBottom() {
  await nextTick()
  if (messageBottomRef.value) {
    messageBottomRef.value.scrollIntoView({ behavior: 'smooth', block: 'end' })
  } else if (messageAreaRef.value) {
    messageAreaRef.value.scrollTop = messageAreaRef.value.scrollHeight
  }
}

// 退出
function handleLogout() {
  authStore.logout()
}
</script>

<style scoped>
/* ===== 布局 ===== */
.chat-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ===== 顶栏 ===== */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
  z-index: 10;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-left h2 { font-size: 18px; color: #303133; white-space: nowrap; }
.sidebar-toggle { padding: 6px; }
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-name { font-size: 14px; color: #606266; }

/* ===== 主体 ===== */
.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* 遮罩 */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 15;
}

/* ===== 侧边栏 ===== */
.chat-sidebar {
  width: 280px;
  min-width: 280px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: margin-left 0.25s ease, opacity 0.25s ease;
  z-index: 20;
}
.chat-sidebar:not(.open) {
  margin-left: -280px;
  opacity: 0;
  pointer-events: none;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
}

.sidebar-search {
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.conv-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f2f3f5;
  transition: background 0.15s;
}
.conv-item:hover { background: #f5f7fa; }
.conv-item.active { background: #ecf5ff; border-left: 3px solid #409eff; }

.conv-main { min-width: 0; }
.conv-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}
.conv-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 20px;
}
.conv-time { font-size: 12px; color: #c0c4cc; }
.conv-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}
.conv-empty {
  padding: 40px 16px;
  text-align: center;
  color: #c0c4cc;
  font-size: 14px;
}

/* ===== 对话主区域 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  min-width: 0;
}

/* ===== 欢迎页 ===== */
.welcome-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  overflow-y: auto;
}
.welcome-icon { font-size: 64px; margin-bottom: 16px; }
.welcome-title { font-size: 24px; color: #303133; margin-bottom: 8px; font-weight: 600; }
.welcome-desc { font-size: 14px; color: #909399; margin-bottom: 40px; }

.quick-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 20px 28px;
  background: #fff;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e4e7ed;
  min-width: 140px;
}
.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  border-color: #409eff;
}
.quick-icon { font-size: 28px; }
.quick-label { font-size: 15px; font-weight: 500; color: #303133; }
.quick-hint { font-size: 12px; color: #c0c4cc; }

.example-questions {
  max-width: 560px;
  width: 100%;
}
.example-questions h3 {
  font-size: 15px;
  color: #606266;
  margin-bottom: 12px;
  text-align: center;
  font-weight: 500;
}
.example-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}
.example-item {
  padding: 10px 18px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 20px;
  font-size: 14px;
  color: #409eff;
  cursor: pointer;
  transition: all 0.15s;
}
.example-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

/* ===== 消息区 ===== */
.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}

.message {
  display: flex;
  margin-bottom: 24px;
  animation: msgIn 0.2s ease-out;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user { flex-direction: row-reverse; }

.message-avatar {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.message.user .message-avatar { margin-left: 12px; }
.message.assistant .message-avatar { margin-right: 12px; }

.message-body {
  max-width: 75%;
  min-width: 80px;
}
.message.user .message-body {
  background: #409eff;
  color: #fff;
  border-radius: 14px 4px 14px 14px;
  padding: 12px 18px;
}
.message.assistant .message-body {
  background: #fff;
  border-radius: 4px 14px 14px 14px;
  padding: 14px 18px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}

.message-content {
  font-size: 15px;
  line-height: 1.8;
  word-break: break-word;
}

/* 用户消息中 markdown 样式适配 */
.message.user .message-content :deep(code) {
  background: rgba(255,255,255,0.2);
  color: #fff;
}
.message.user .message-content :deep(a) { color: #fff; text-decoration: underline; }

/* 助手消息 Markdown 渲染 */
.message.assistant .message-content :deep(p) { margin: 0 0 8px; }
.message.assistant .message-content :deep(p:last-child) { margin-bottom: 0; }
.message.assistant .message-content :deep(ul), .message-content :deep(ol) { padding-left: 20px; margin: 6px 0; }
.message.assistant .message-content :deep(li) { margin: 3px 0; }
.message.assistant .message-content :deep(h1), .message-content :deep(h2), .message-content :deep(h3) {
  margin: 12px 0 6px;
  font-weight: 600;
}
.message.assistant .message-content :deep(h2) { font-size: 17px; }
.message.assistant .message-content :deep(h3) { font-size: 15px; }
.message.assistant .message-content :deep(blockquote) {
  border-left: 3px solid #dcdfe6;
  padding: 4px 12px;
  margin: 8px 0;
  color: #909399;
}
.message.assistant .message-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}
.message.assistant .message-content :deep(th), .message-content :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 6px 12px;
  text-align: left;
}
.message.assistant .message-content :deep(th) { background: #f5f7fa; font-weight: 500; }
.message.assistant .message-content :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  font-size: 13px;
  line-height: 1.6;
}
.message.assistant .message-content :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 13px;
  color: inherit;
}
.message.assistant .message-content :deep(code) {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #e74c3c;
}
.message.assistant .message-content :deep(a) {
  color: #409eff;
  text-decoration: none;
}
.message.assistant .message-content :deep(a:hover) { text-decoration: underline; }

/* 引用来源 */
.message-sources { margin-top: 14px; }
.message-sources :deep(.el-divider__text) {
  font-size: 13px;
  background: #fff;
}
.source-item {
  margin-bottom: 8px;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}
.source-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.source-filename { font-size: 13px; font-weight: 500; color: #303133; }
.source-page { font-size: 12px; color: #909399; }
.source-snippet {
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
}

/* 消息操作 */
.message-actions {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 4px;
}
.message-actions .el-button {
  color: #909399;
  font-size: 12px;
}
.message-actions .el-button:hover {
  color: #409eff;
}

/* 流式光标 */
.streaming-cursor {
  display: inline;
  animation: blink 1s infinite;
  font-size: 16px;
  color: #409eff;
  margin-left: 2px;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== 输入区 ===== */
.input-area {
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
}
.input-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.chat-input {
  flex: 1;
}
.send-btn {
  height: 40px;
  width: 48px;
  flex-shrink: 0;
}
.send-btn .el-icon { margin: 0; }
.input-hint {
  text-align: right;
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 6px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .chat-sidebar {
    position: fixed;
    top: 56px;
    left: 0;
    bottom: 0;
    box-shadow: 2px 0 12px rgba(0,0,0,0.15);
  }
  .chat-sidebar:not(.open) {
    margin-left: -280px;
  }
  .sidebar-overlay { display: block; }

  .header-left h2 { font-size: 16px; }
  .header-right .user-name { display: none; }

  .message-body { max-width: 85%; }
  .message-area { padding: 16px; }
  .input-area { padding: 12px 16px; }

  .welcome-area { padding: 24px 16px; }
  .quick-actions { flex-direction: column; }
  .quick-card { flex-direction: row; gap: 12px; min-width: auto; width: 100%; max-width: 300px; }
  .example-list { flex-direction: column; align-items: center; }
}
</style>
