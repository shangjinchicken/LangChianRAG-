import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/Register.vue'),
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/chat/:id',
      name: 'ChatDetail',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('../views/AdminView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// 导航守卫：未登录跳转登录页，非管理员跳转首页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')

  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  if (to.meta.requiresAdmin) {
    if (!userStr) {
      next('/chat')
      return
    }
    try {
      const user = JSON.parse(userStr)
      if (user.role !== 'admin') {
        next('/chat')
        return
      }
    } catch {
      next('/chat')
      return
    }
  }

  // 已登录用户访问登录/注册页，重定向到聊天页
  if ((to.path === '/login' || to.path === '/register') && token) {
    next('/chat')
    return
  }

  next()
})

export default router
