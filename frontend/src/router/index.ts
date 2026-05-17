import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/modules/blog/views/HomeView.vue'),
    meta: { title: '进击の卡卡罗特', standalone: true },
  },
  {
    path: '/article/:slug',
    name: 'Article',
    component: () => import('@/modules/blog/views/ArticleView.vue'),
    meta: { title: '文章详情' },
  },
  {
    path: '/category/:id',
    name: 'Category',
    component: () => import('@/modules/blog/views/CategoryView.vue'),
    meta: { title: '分类' },
  },
  {
    path: '/tag/:id',
    name: 'Tag',
    component: () => import('@/modules/blog/views/TagView.vue'),
    meta: { title: '标签' },
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/modules/blog/views/SearchView.vue'),
    meta: { title: '搜索' },
  },
  {
    path: '/messages',
    name: 'Messages',
    component: () => import('@/modules/blog/views/MessageWallView.vue'),
    meta: { title: '留言墙' },
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/modules/blog/views/AboutMeView.vue'),
    meta: { title: '关于我' },
  },

  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/modules/admin/views/LoginView.vue'),
    meta: { title: '管理员登录', noAuth: true },
  },
  {
    path: '/admin',
    redirect: '/admin/dashboard',
    component: () => import('@/modules/admin/components/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/modules/admin/views/DashboardView.vue'),
        meta: { title: '仪表盘', requiresAuth: true },
      },
      {
        path: 'articles',
        name: 'Articles',
        component: () => import('@/modules/admin/views/ArticlesView.vue'),
        meta: { title: '文章管理', requiresAuth: true, keepAlive: true },
      },
      {
        path: 'articles/new',
        name: 'ArticleNew',
        component: () => import('@/modules/admin/views/ArticleEditorView.vue'),
        meta: { title: '新建文章', requiresAuth: true },
      },
      {
        path: 'articles/edit/:id',
        name: 'ArticleEdit',
        component: () => import('@/modules/admin/views/ArticleEditorView.vue'),
        meta: { title: '编辑文章', requiresAuth: true },
      },
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('@/modules/admin/views/CategoriesView.vue'),
        meta: { title: '分类管理', requiresAuth: true },
      },
      {
        path: 'tags',
        name: 'Tags',
        component: () => import('@/modules/admin/views/TagsView.vue'),
        meta: { title: '标签管理', requiresAuth: true },
      },
      {
        path: 'comments',
        name: 'Comments',
        component: () => import('@/modules/admin/views/CommentsView.vue'),
        meta: { title: '评论管理', requiresAuth: true, keepAlive: true },
      },
      {
        path: 'guestbook',
        name: 'GuestbookManage',
        component: () => import('@/modules/admin/views/GuestbookManageView.vue'),
        meta: { title: '留言管理', requiresAuth: true },
      },
      {
        path: 'system-config',
        name: 'SystemConfig',
        component: () => import('@/modules/admin/views/SystemConfigView.vue'),
        meta: { title: '系统配置', requiresAuth: true },
      },
      {
        path: 'sensitive-words',
        name: 'SensitiveWords',
        component: () => import('@/modules/admin/views/SensitiveWordsView.vue'),
        meta: { title: '敏感词管理', requiresAuth: true },
      },
      {
        path: 'operation-logs',
        name: 'OperationLogs',
        component: () => import('@/modules/admin/views/OperationLogsView.vue'),
        meta: { title: '操作日志', requiresAuth: true, keepAlive: true },
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/modules/admin/views/StatisticsView.vue'),
        meta: { title: '数据统计', requiresAuth: true },
      },
    ],
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/modules/blog/views/NotFoundView.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.title) {
    if (to.meta.standalone) {
      document.title = to.meta.title as string
    } else {
      document.title = `${to.meta.title}`
    }
  }

  if (to.name === 'AdminLogin' && authStore.isAuthenticated) {
    try {
      if (!authStore.adminInfo) {
        await authStore.fetchAdminInfo()
      }
      next({ name: 'Dashboard' })
    } catch (error) {
      await authStore.logout(false)
      next()
    }
    return
  }

  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      next({
        name: 'AdminLogin',
        query: { redirect: to.fullPath },
      })
      return
    }

    if (!authStore.adminInfo) {
      try {
        await authStore.fetchAdminInfo()
        next()
      } catch (error) {
        await authStore.logout(false)
        next({
          name: 'AdminLogin',
          query: { redirect: to.fullPath },
        })
      }
      return
    }
  }

  next()
})

export default router
