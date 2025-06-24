<template>
  <div id="app">
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header v-if="!isLoginPage" class="app-header">
        <div class="header-content">
          <div class="logo">
            <h2>视觉矩阵</h2>
          </div>
          <el-menu
            :default-active="activeMenu"
            class="header-menu"
            mode="horizontal"
            @select="handleMenuSelect"
          >
            <el-menu-item index="/">首页</el-menu-item>
            <el-menu-item index="/dashboard" v-if="isLoggedIn">工作台</el-menu-item>
            <el-menu-item index="/gallery" v-if="isLoggedIn">我的作品</el-menu-item>
          </el-menu>
          <div class="header-right">
            <template v-if="isLoggedIn">
              <span class="points">积分: {{ userPoints }}</span>
              <el-dropdown @command="handleUserMenu">
                <span class="el-dropdown-link">
                  {{ username }}
                  <el-icon class="el-icon--right">
                    <arrow-down />
                  </el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                    <el-dropdown-item command="recharge">充值中心</el-dropdown-item>
                    <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <template v-else>
              <el-button type="primary" @click="$router.push('/login')">登录</el-button>
            </template>
          </div>
        </div>
      </el-header>

      <!-- 主内容区域 -->
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    ArrowDown
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    const username = ref('')
    const userPoints = ref(0)
    const isLoggedIn = ref(false)
    
    const isLoginPage = computed(() => route.path === '/login')
    const activeMenu = computed(() => route.path)
    
    // 检查登录状态
    const checkLoginStatus = () => {
      const token = localStorage.getItem('token')
      if (token) {
        // 这里应该调用API验证token有效性
        const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
        username.value = userInfo.username || ''
        userPoints.value = userInfo.points || 0
        isLoggedIn.value = true
      }
    }
    
    const handleMenuSelect = (index) => {
      router.push(index)
    }
    
    const handleUserMenu = (command) => {
      switch (command) {
        case 'profile':
          // 打开个人资料
          break
        case 'recharge':
          // 打开充值中心
          break
        case 'logout':
          logout()
          break
      }
    }
    
    const logout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      isLoggedIn.value = false
      router.push('/')
    }
    
    onMounted(() => {
      checkLoginStatus()
    })
    
    return {
      username,
      userPoints,
      isLoggedIn,
      isLoginPage,
      activeMenu,
      handleMenuSelect,
      handleUserMenu
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.logo h2 {
  margin: 0;
  color: #409eff;
}

.header-menu {
  border-bottom: none;
  flex: 1;
  margin-left: 40px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.points {
  color: #409eff;
  font-weight: bold;
}

.el-dropdown-link {
  cursor: pointer;
  color: #409eff;
  display: flex;
  align-items: center;
}

.app-main {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 60px);
}
</style>