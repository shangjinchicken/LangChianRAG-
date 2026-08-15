<template>
  <div class="profile-layout">
    <header class="profile-header">
      <h2>👤 个人中心</h2>
      <div>
        <el-button @click="$router.push('/chat')">返回问答</el-button>
      </div>
    </header>

    <div class="profile-content">
      <el-card class="info-card">
        <template #header>
          <span>基本信息</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ authStore.user?.username }}</el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag :type="authStore.isAdmin ? 'danger' : 'info'" size="small">
              {{ authStore.isAdmin ? '管理员' : '普通用户' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ authStore.user?.email || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ authStore.user?.created_at ? new Date(authStore.user.created_at).toLocaleDateString('zh-CN') : '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="password-card">
        <template #header>
          <span>修改密码</span>
        </template>
        <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width: 420px">
          <el-form-item label="旧密码" prop="old_password">
            <el-input v-model="form.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="form.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input v-model="form.confirm_password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="handleChangePassword">修改密码</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { authAPI } from '../api'

const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirm = (_rule: any, value: string, callback: any) => {
  if (value !== form.new_password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function handleChangePassword() {
  loading.value = true
  try {
    await authAPI.changePassword({
      old_password: form.old_password,
      new_password: form.new_password,
    })
    ElMessage.success('密码修改成功')
    form.old_password = ''
    form.new_password = ''
    form.confirm_password = ''
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '密码修改失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}
.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.profile-content {
  padding: 24px;
  max-width: 700px;
}
.password-card {
  margin-top: 20px;
}
</style>
