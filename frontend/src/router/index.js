import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import Documents from '../views/Documents.vue'
import DocumentForm from '../views/DocumentForm.vue'
import Calendar from '../views/Calendar.vue'
import Reminders from '../views/Reminders.vue'
import Guides from '../views/Guides.vue'
import Family from '../views/Family.vue'
import Settings from '../views/Settings.vue'
import AdminGuides from '../views/AdminGuides.vue'
import { getToken } from '../api'

const routes = [
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', name: 'dashboard', component: Dashboard, meta: { title: '首页' } },
      { path: 'documents', name: 'documents', component: Documents, meta: { title: '我的证件' } },
      { path: 'documents/new', name: 'doc-new', component: DocumentForm, meta: { title: '添加证件' } },
      { path: 'documents/:id/edit', name: 'doc-edit', component: DocumentForm, meta: { title: '编辑证件' } },
      { path: 'calendar', name: 'calendar', component: Calendar, meta: { title: '到期日历' } },
      { path: 'reminders', name: 'reminders', component: Reminders, meta: { title: '提醒中心' } },
      { path: 'guides', name: 'guides', component: Guides, meta: { title: '续办指南' } },
      { path: 'family', name: 'family', component: Family, meta: { title: '家庭提醒' } },
      { path: 'settings', name: 'settings', component: Settings, meta: { title: '设置' } },
      { path: 'admin/guides', name: 'admin-guides', component: AdminGuides, meta: { title: '指南维护', admin: true } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.path.startsWith('/login') || to.path.startsWith('/register')) {
    return getToken() ? { path: '/' } : true
  }
  if (!getToken()) return { path: '/login' }
  return true
})

export default router