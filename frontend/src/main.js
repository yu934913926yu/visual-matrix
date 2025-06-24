import App from './App.vue'
import Home from './views/Home.vue'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Gallery from './views/Gallery.vue'
import Recharge from './views/Recharge.vue'
import Admin from './views/Admin.vue'

// 路由配置
const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/gallery', component: Gallery, meta: { requiresAuth: true } },
  { path: '/recharge', component: Recharge, meta: { requiresAuth: true } },
  { path: '/admin', component: Admin, meta: { requiresAuth: true, requiresAdmin: true } }
]