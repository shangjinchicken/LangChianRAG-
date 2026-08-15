<template>
  <div class="admin-layout">
    <!-- 顶部导航 -->
    <header class="admin-header">
      <div class="header-left">
        <el-button text @click="$router.push('/chat')" style="margin-right: 8px">
          <el-icon :size="18"><ArrowLeft /></el-icon>
        </el-button>
        <h2>📂 知识库管理</h2>
      </div>
      <div>
        <el-button @click="$router.push('/chat')" type="primary" plain>返回问答</el-button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: #ecf5ff">
          <el-icon :size="24" color="#409eff"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-number">{{ stats.document_count }}</div>
          <div class="stat-label">文档总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #fef0f0">
          <el-icon :size="24" color="#f56c6c"><Grid /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-number">{{ stats.total_chunks }}</div>
          <div class="stat-label">片段总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #f0f9eb">
          <el-icon :size="24" color="#67c23a"><Coin /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-number">{{ formatSize(stats.total_size) }}</div>
          <div class="stat-label">存储大小</div>
        </div>
        <div class="stat-card-tip">自动向量化存储</div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <!-- 上传按钮 -->
        <el-upload
          ref="uploadRef"
          :before-upload="handleUpload"
          :show-file-list="false"
          accept=".pdf,.docx,.xlsx,.xls,.txt,.md,.csv"
          multiple
        >
          <el-button type="primary" :icon="Upload">上传文档</el-button>
        </el-upload>
        <el-popover placement="bottom" :width="300" trigger="hover">
          <template #reference>
            <el-button text circle :icon="QuestionFilled" />
          </template>
          <div class="upload-guide">
            <h4>📋 支持的文件格式</h4>
            <ul>
              <li>📄 PDF, Word (.docx)</li>
              <li>📊 Excel (.xlsx, .xls)</li>
              <li>📝 文本文件 (.txt, .md, .csv)</li>
            </ul>
            <p style="color: #909399; font-size: 12px; margin-top: 8px">单文件最大 20MB，支持多文件同时上传</p>
          </div>
        </el-popover>
        <!-- 批量操作 -->
        <el-button
          v-if="selectedIds.length > 0"
          type="danger"
          plain
          @click="handleBatchDelete"
        >
          删除选中 ({{ selectedIds.length }})
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文档名称..."
          size="default"
          clearable
          :prefix-icon="Search"
          class="doc-search"
        />
        <el-button text :icon="Refresh" @click="refreshAll" title="刷新" />
      </div>
    </div>

    <!-- 拖拽上传区域 -->
    <div
      :class="['drop-zone', { 'drop-active': isDragging }]"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <div class="drop-content">
        <el-icon :size="36" color="#c0c4cc"><UploadFilled /></el-icon>
        <p>拖拽文件到此处上传</p>
        <p class="drop-hint">支持 PDF、Word、Excel、TXT、Markdown、CSV · 最大 20MB</p>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="doc-table">
      <el-table
        :data="filteredDocuments"
        stripe
        v-loading="loading"
        empty-text="暂无文档，请上传文件到知识库"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="40" align="center" />
        <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="filename-cell">
              <span class="file-icon">{{ getFileIcon(row.file_type) }}</span>
              <span class="file-name">{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getFileTypeColor(row.file_type)">{{ row.file_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100" align="center">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="片段数" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="warning" v-if="row.chunk_count > 0">{{ row.chunk_count }}</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="row.status === 'processing'" type="warning" size="small">
              <el-icon class="is-loading" :size="12"><Loading /></el-icon>
              处理中
            </el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger" size="small">失败</el-tag>
            <el-tag v-else type="info" size="small">待处理</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上传时间" width="160" align="center">
          <template #default="{ row }">{{ formatTime(row.uploaded_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" type="primary" @click="handleReprocess(row)">重处理</el-button>
            <el-popconfirm title="确认删除此文档？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button text size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadDocuments"
          background
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, Search, Refresh, UploadFilled, QuestionFilled,
  ArrowLeft, Document, Grid, Coin, Loading,
} from '@element-plus/icons-vue'
import { knowledgeAPI } from '../api'

const documents = ref<any[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const selectedIds = ref<string[]>([])
const isDragging = ref(false)
const uploadRef = ref()

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const stats = reactive({ document_count: 0, total_chunks: 0, total_size: 0 })

// 过滤文档
const filteredDocuments = computed(() => {
  if (!searchKeyword.value) return documents.value
  const kw = searchKeyword.value.toLowerCase()
  return documents.value.filter(d => d.filename.toLowerCase().includes(kw))
})

onMounted(() => {
  refreshAll()
})

async function loadDocuments() {
  loading.value = true
  try {
    const res = await knowledgeAPI.listDocuments({ page: pagination.page, pageSize: pagination.pageSize })
    documents.value = res.data.items
    pagination.total = res.data.total
  } catch {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const res = await knowledgeAPI.getStats()
    Object.assign(stats, res.data)
  } catch {}
}

function refreshAll() {
  loadDocuments()
  loadStats()
}

// 选择
function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map(r => r.id)
}

// 上传
async function handleUpload(file: File) {
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error(`"${file.name}" 超过 20MB 限制`)
    return false
  }
  try {
    await knowledgeAPI.upload(file)
    ElMessage.success(`"${file.name}" 上传成功，正在向量化处理...`)
    refreshAll()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || `"${file.name}" 上传失败`)
  }
  return false
}

// 拖拽上传
async function handleDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (!files || files.length === 0) return

  for (const file of Array.from(files)) {
    await handleUpload(file)
  }
}

// 批量删除
async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${selectedIds.value.length} 个文档？此操作不可恢复。`,
      '批量删除',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
    for (const id of selectedIds.value) {
      await knowledgeAPI.deleteDocument(id)
    }
    ElMessage.success(`已删除 ${selectedIds.value.length} 个文档`)
    selectedIds.value = []
    refreshAll()
  } catch {
    // 用户取消
  }
}

// 删除单个
async function handleDelete(id: string) {
  try {
    await knowledgeAPI.deleteDocument(id)
    ElMessage.success('文档已删除')
    refreshAll()
  } catch {
    ElMessage.error('删除失败')
  }
}

// 重处理
async function handleReprocess(row: any) {
  try {
    await knowledgeAPI.reprocess(row.id)
    ElMessage.success('已触发重新处理')
    setTimeout(() => refreshAll(), 2000)
  } catch {
    ElMessage.error('重新处理失败')
  }
}

// 工具函数
function formatSize(bytes: number): string {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + units[i]
}

function formatTime(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

function getFileIcon(type: string): string {
  const map: Record<string, string> = {
    pdf: '📄', docx: '📝', doc: '📝',
    xlsx: '📊', xls: '📊', csv: '📋',
    txt: '📃', md: '📝',
  }
  return map[type] || '📎'
}

function getFileTypeColor(type: string): string {
  const map: Record<string, string> = {
    pdf: 'danger', docx: 'primary', doc: 'primary',
    xlsx: 'success', xls: 'success', csv: 'warning',
  }
  return map[type] || 'info'
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 顶栏 */
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
}
.admin-header h2 { font-size: 18px; color: #303133; }

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  padding: 20px 24px;
  flex-shrink: 0;
}
.stat-card {
  flex: 1;
  background: #fff;
  padding: 20px 24px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s;
  position: relative;
}
.stat-card:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-number {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.stat-card-tip {
  position: absolute;
  bottom: 8px;
  right: 16px;
  font-size: 11px;
  color: #c0c4cc;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px 12px;
  flex-shrink: 0;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-search {
  width: 220px;
}

/* 上传引导 */
.upload-guide h4 { margin: 0 0 8px; font-size: 14px; }
.upload-guide ul { padding-left: 16px; margin: 0; font-size: 13px; color: #606266; }
.upload-guide li { margin: 4px 0; }

/* 拖拽上传区域 */
.drop-zone {
  margin: 0 24px 12px;
  padding: 24px;
  border: 2px dashed #dcdfe6;
  border-radius: 10px;
  text-align: center;
  transition: all 0.2s;
  cursor: pointer;
  flex-shrink: 0;
}
.drop-zone:hover,
.drop-zone.drop-active {
  border-color: #409eff;
  background: #ecf5ff;
}
.drop-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.drop-content p {
  margin: 0;
  font-size: 14px;
  color: #606266;
}
.drop-hint {
  font-size: 12px !important;
  color: #c0c4cc !important;
}

/* 文档表格 */
.doc-table {
  flex: 1;
  padding: 0 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.doc-table :deep(.el-table) {
  flex: 1;
}
.doc-table :deep(.el-table__body-wrapper) {
  flex: 1;
}

.filename-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-icon { font-size: 18px; }
.file-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-row { flex-direction: column; padding: 12px 16px; gap: 8px; }
  .toolbar { flex-direction: column; gap: 8px; padding: 0 16px 12px; }
  .toolbar-left, .toolbar-right { width: 100%; }
  .doc-search { width: 100%; }
  .doc-table { padding: 0 12px; }
  .drop-zone { margin: 0 12px 12px; }
  .admin-header h2 { font-size: 16px; }
}
</style>
