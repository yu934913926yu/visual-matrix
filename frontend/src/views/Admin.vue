])
    const userSearch = ref('')
    const loadingUsers = ref(false)
    const userPagination = reactive({
      page: 1,
      per_page: 20,
      total: 0
    })
    const showPointsDialog = ref(false)
    const currentUser = ref(null)
    const pointsForm = reactive({
      adjustment: 0,
      reason: ''
    })
    
    // 系统配置
    const systemConfig = reactive({
      new_user_bonus_points: 50,
      base_generation_cost: 10,
      analyze_cost: 1,
      cny_to_points_rate: 30
    })
    const savingConfig = ref(false)
    
    // 风格模板
    const styleTemplates = ref([])
    const loadingTemplates = ref(false)
    const showTemplateDialog = ref(false)
    const editingTemplate = ref(null)
    const templateForm = reactive({
      name: '',
      description: '',
      thumbnail_url: '',
      prompt_instruction: '',
      sort_order: 0,
      is_active: true
    })
    
    // API通道
    const apiChannels = ref([])
    const showChannelDialog = ref(false)
    const testingChannel = ref(null)
    
    // 加载数据总览
    const loadDashboardStats = async () => {
      try {
        loadingStats.value = true
        const token = localStorage.getItem('token')
        const response = await axios.get('/admin/dashboard/stats', {
          headers: { Authorization: `Bearer ${token}` }
        })
        stats.value = response.data
      } catch (error) {
        ElMessage.error('加载统计数据失败')
      } finally {
        loadingStats.value = false
      }
    }
    
    // 加载用户列表
    const loadUsers = async () => {
      try {
        loadingUsers.value = true
        const token = localStorage.getItem('token')
        const response = await axios.get('/admin/users', {
          params: {
            page: userPagination.page,
            per_page: userPagination.per_page,
            search: userSearch.value
          },
          headers: { Authorization: `Bearer ${token}` }
        })
        users.value = response.data.users
        Object.assign(userPagination, response.data.pagination)
      } catch (error) {
        ElMessage.error('加载用户列表失败')
      } finally {
        loadingUsers.value = false
      }
    }
    
    // 搜索用户
    const searchUsers = () => {
      userPagination.page = 1
      loadUsers()
    }
    
    // 调整积分
    const adjustPoints = (user) => {
      currentUser.value = user
      pointsForm.adjustment = 0
      pointsForm.reason = ''
      showPointsDialog.value = true
    }
    
    const confirmAdjustPoints = async () => {
      if (!pointsForm.reason) {
        ElMessage.warning('请输入调整原因')
        return
      }
      
      try {
        const token = localStorage.getItem('token')
        await axios.post(`/admin/users/${currentUser.value.id}/points`, {
          adjustment: pointsForm.adjustment,
          reason: pointsForm.reason
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        ElMessage.success('积分调整成功')
        showPointsDialog.value = false
        loadUsers()
      } catch (error) {
        ElMessage.error('积分调整失败')
      }
    }
    
    // 设置会员
    const setMembership = async (user) => {
      // 这里可以打开一个新的对话框来设置会员等级和有效期
      ElMessage.info('会员设置功能开发中...')
    }
    
    // 加载系统配置
    const loadSystemConfig = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/admin/system-config', {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        const configs = response.data.configs
        for (const key in configs) {
          if (systemConfig.hasOwnProperty(key)) {
            systemConfig[key] = parseInt(configs[key].value) || configs[key].value
          }
        }
      } catch (error) {
        ElMessage.error('加载系统配置失败')
      }
    }
    
    // 保存系统配置
    const saveSystemConfig = async () => {
      try {
        savingConfig.value = true
        const token = localStorage.getItem('token')
        await axios.post('/admin/system-config', {
          configs: {
            new_user_bonus_points: String(systemConfig.new_user_bonus_points),
            base_generation_cost: String(systemConfig.base_generation_cost),
            analyze_cost: String(systemConfig.analyze_cost),
            cny_to_points_rate: String(systemConfig.cny_to_points_rate)
          }
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        ElMessage.success('配置保存成功')
      } catch (error) {
        ElMessage.error('配置保存失败')
      } finally {
        savingConfig.value = false
      }
    }
    
    // 加载风格模板
    const loadStyleTemplates = async () => {
      try {
        loadingTemplates.value = true
        const token = localStorage.getItem('token')
        const response = await axios.get('/admin/style-templates', {
          headers: { Authorization: `Bearer ${token}` }
        })
        styleTemplates.value = response.data.templates
      } catch (error) {
        ElMessage.error('加载风格模板失败')
      } finally {
        loadingTemplates.value = false
      }
    }
    
    // 编辑模板
    const editTemplate = (template) => {
      editingTemplate.value = template
      Object.assign(templateForm, template)
      showTemplateDialog.value = true
    }
    
    // 保存模板
    const saveTemplate = async () => {
      try {
        const token = localStorage.getItem('token')
        
        if (editingTemplate.value) {
          // 更新
          await axios.put(`/admin/style-templates/${editingTemplate.value.id}`, templateForm, {
            headers: { Authorization: `Bearer ${token}` }
          })
        } else {
          // 创建
          await axios.post('/admin/style-templates', templateForm, {
            headers: { Authorization: `Bearer ${token}` }
          })
        }
        
        ElMessage.success('保存成功')
        showTemplateDialog.value = false
        loadStyleTemplates()
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }
    
    // 删除模板
    const deleteTemplate = async (template) => {
      try {
        await ElMessageBox.confirm('确定删除该风格模板吗？', '提示', {
          type: 'warning'
        })
        
        const token = localStorage.getItem('token')
        await axios.delete(`/admin/style-templates/${template.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        ElMessage.success('删除成功')
        loadStyleTemplates()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    // 切换模板状态
    const toggleTemplateStatus = async (template) => {
      try {
        const token = localStorage.getItem('token')
        await axios.put(`/admin/style-templates/${template.id}`, {
          is_active: template.is_active
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        ElMessage.success('状态更新成功')
      } catch (error) {
        template.is_active = !template.is_active
        ElMessage.error('状态更新失败')
      }
    }
    
    // 加载API通道
    const loadApiChannels = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/admin/api-channels', {
          headers: { Authorization: `Bearer ${token}` }
        })
        apiChannels.value = response.data.channels
      } catch (error) {
        ElMessage.error('加载API通道失败')
      }
    }
    
    // 测试通道
    const testChannel = async (channel) => {
      try {
        testingChannel.value = channel.id
        const token = localStorage.getItem('token')
        const response = await axios.post(`/admin/api-channels/${channel.id}/test`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        channel.is_healthy = response.data.is_healthy
        channel.latency_ms = response.data.latency_ms
        
        ElMessage.success(`测试完成，延迟：${response.data.latency_ms}ms`)
      } catch (error) {
        ElMessage.error('测试失败')
      } finally {
        testingChannel.value = null
      }
    }
    
    // 切换通道状态
    const toggleChannelStatus = async (channel) => {
      // 这里应该调用API更新通道状态
      ElMessage.info('通道状态更新功能开发中...')
    }
    
    // 编辑通道
    const editChannel = (channel) => {
      ElMessage.info('通道编辑功能开发中...')
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    // 处理菜单选择
    const handleMenuSelect = (index) => {
      activeMenu.value = index
    }
    
    // 监听菜单变化，加载对应数据
    watch(activeMenu, (newValue) => {
      switch (newValue) {
        case 'dashboard':
          loadDashboardStats()
          break
        case 'users':
          loadUsers()
          break
        case 'system-config':
          loadSystemConfig()
          break
        case 'style-templates':
          loadStyleTemplates()
          break
        case 'api-channels':
          loadApiChannels()
          break
      }
    })
    
    onMounted(() => {
      // 检查管理员权限
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      if (userInfo.role !== 'admin') {
        ElMessage.error('无权访问管理后台')
        // 跳转回首页
        window.location.href = '/'
        return
      }
      
      // 加载初始数据
      loadDashboardStats()
    })
    
    return {
      activeMenu,
      stats,
      loadingStats,
      users,
      userSearch,
      loadingUsers,
      userPagination,
      showPointsDialog,
      currentUser,
      pointsForm,
      systemConfig,
      savingConfig,
      styleTemplates,
      loadingTemplates,
      showTemplateDialog,
      editingTemplate,
      templateForm,
      apiChannels,
      showChannelDialog,
      testingChannel,
      handleMenuSelect,
      searchUsers,
      adjustPoints,
      confirmAdjustPoints,
      setMembership,
      saveSystemConfig,
      editTemplate,
      saveTemplate,
      deleteTemplate,
      toggleTemplateStatus,
      testChannel,
      toggleChannelStatus,
      editChannel,
      formatDate
    }
  }
}
</script>

<style scoped>
.admin-container {
  height: 100vh;
  background: #f0f2f5;
}

.admin-sidebar {
  background-color: #304156;
  height: 100vh;
  overflow-y: auto;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h3 {
  color: white;
  margin: 0;
  font-size: 16px;
}

.admin-main {
  padding: 20px;
  overflow-y: auto;
}

/* 数据总览 */
.dashboard-section h2 {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 25px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-change {
  font-size: 12px;
  color: #606266;
}

.change-number {
  color: #67c23a;
  font-weight: 500;
}

/* 工具栏 */
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

/* 表格样式 */
.el-table {
  margin-bottom: 20px;
}

.points-number {
  font-weight: bold;
  color: #409eff;
}

.text-muted {
  color: #909399;
}

/* 表单提示 */
.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

/* API通道网格 */
.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.channel-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
}

.channel-card.unhealthy {
  border: 2px solid #f56c6c;
}

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.channel-header h4 {
  margin: 0;
  font-size: 18px;
}

.channel-info {
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-item span:first-child {
  color: #909399;
  min-width: 80px;
}

.info-value {
  color: #606266;
  word-break: break-all;
}

.channel-models {
  margin-bottom: 15px;
}

.channel-models h5 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.models-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.channel-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}
</style>        <el-form-item label="提示词指令" required>
          <el-input
            v-model="templateForm.prompt_instruction"
            type="textarea"
            :rows="6"
            placeholder="请输入风格对应的AI提示词指令..."
          />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="templateForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="templateForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  DataLine,
  User,
  List,
  Setting,
  Brush,
  Wallet,
  Trophy,
  Connection,
  Picture,
  Coin,
  Search,
  Plus
} from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'Admin',
  components: {
    DataLine,
    User,
    List,
    Setting,
    Brush,
    Wallet,
    Trophy,
    Connection,
    Picture,
    Coin,
    Search,
    Plus
  },
  setup() {
    const activeMenu = ref('dashboard')
    
    // 数据总览
    const stats = ref({})
    const loadingStats = ref(false)
    
    // 用户管理
    const users = ref([<template>
  <div class="admin-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="200px" class="admin-sidebar">
        <div class="logo">
          <h3>视觉矩阵管理后台</h3>
        </div>
        <el-menu
          :default-active="activeMenu"
          @select="handleMenuSelect"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409eff"
        >
          <el-menu-item index="dashboard">
            <el-icon><data-line /></el-icon>
            <span>数据总览</span>
          </el-menu-item>
          <el-menu-item index="users">
            <el-icon><user /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="tasks">
            <el-icon><list /></el-icon>
            <span>任务管理</span>
          </el-menu-item>
          <el-menu-item index="system-config">
            <el-icon><setting /></el-icon>
            <span>系统配置</span>
          </el-menu-item>
          <el-menu-item index="style-templates">
            <el-icon><brush /></el-icon>
            <span>风格模板</span>
          </el-menu-item>
          <el-menu-item index="recharge-packages">
            <el-icon><wallet /></el-icon>
            <span>充值包管理</span>
          </el-menu-item>
          <el-menu-item index="membership-tiers">
            <el-icon><trophy /></el-icon>
            <span>会员等级</span>
          </el-menu-item>
          <el-menu-item index="api-channels">
            <el-icon><connection /></el-icon>
            <span>API通道</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="admin-main">
        <!-- 数据总览 -->
        <div v-if="activeMenu === 'dashboard'" class="dashboard-section">
          <h2>数据总览</h2>
          <div class="stats-grid" v-loading="loadingStats">
            <div class="stat-card">
              <div class="stat-icon" style="background: #409eff;">
                <el-icon><user /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ stats.basic_stats?.total_users || 0 }}</div>
                <div class="stat-label">总用户数</div>
                <div class="stat-change">
                  今日新增：<span class="change-number">+{{ stats.today_stats?.new_users || 0 }}</span>
                </div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: #67c23a;">
                <el-icon><picture /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ stats.basic_stats?.total_tasks || 0 }}</div>
                <div class="stat-label">总任务数</div>
                <div class="stat-change">
                  今日新增：<span class="change-number">+{{ stats.today_stats?.new_tasks || 0 }}</span>
                </div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: #e6a23c;">
                <el-icon><coin /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">¥{{ stats.week_stats?.revenue || 0 }}</div>
                <div class="stat-label">本周收入</div>
                <div class="stat-change">
                  今日收入：<span class="change-number">¥{{ stats.today_stats?.revenue || 0 }}</span>
                </div>
              </div>
            </div>
            
            <div class="stat-card">
              <div class="stat-icon" style="background: #f56c6c;">
                <el-icon><connection /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ stats.api_health?.healthy_channels || 0 }}/{{ stats.api_health?.total_channels || 0 }}</div>
                <div class="stat-label">API健康度</div>
                <div class="stat-change">
                  健康率：<span class="change-number">{{ stats.api_health?.health_rate?.toFixed(1) || 0 }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 用户管理 -->
        <div v-if="activeMenu === 'users'" class="users-section">
          <h2>用户管理</h2>
          <div class="toolbar">
            <el-input
              v-model="userSearch"
              placeholder="搜索用户名"
              clearable
              style="width: 300px"
              @keyup.enter="searchUsers"
            >
              <template #prefix>
                <el-icon><search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="searchUsers">搜索</el-button>
          </div>
          
          <el-table :data="users" v-loading="loadingUsers" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="points" label="积分余额">
              <template #default="scope">
                <span class="points-number">{{ scope.row.points }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="role" label="角色">
              <template #default="scope">
                <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'">
                  {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="membership_tier_id" label="会员状态">
              <template #default="scope">
                <el-tag v-if="scope.row.membership_tier_id" type="warning">
                  VIP会员
                </el-tag>
                <span v-else class="text-muted">普通用户</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button
                  type="primary"
                  size="small"
                  @click="adjustPoints(scope.row)"
                >
                  调整积分
                </el-button>
                <el-button
                  type="warning"
                  size="small"
                  @click="setMembership(scope.row)"
                >
                  设置会员
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-model:current-page="userPagination.page"
            v-model:page-size="userPagination.per_page"
            :total="userPagination.total"
            layout="total, prev, pager, next, jumper"
            @current-change="loadUsers"
          />
        </div>

        <!-- 系统配置 -->
        <div v-if="activeMenu === 'system-config'" class="config-section">
          <h2>系统配置</h2>
          <el-form :model="systemConfig" label-width="200px">
            <el-form-item label="新用户注册赠送积分">
              <el-input-number
                v-model="systemConfig.new_user_bonus_points"
                :min="0"
                :max="1000"
              />
            </el-form-item>
            <el-form-item label="单张图片生成基础成本">
              <el-input-number
                v-model="systemConfig.base_generation_cost"
                :min="1"
                :max="100"
              />
              <span class="form-tip">积分</span>
            </el-form-item>
            <el-form-item label="图片分析消耗积分">
              <el-input-number
                v-model="systemConfig.analyze_cost"
                :min="0"
                :max="10"
              />
              <span class="form-tip">积分</span>
            </el-form-item>
            <el-form-item label="1元对应积分数">
              <el-input-number
                v-model="systemConfig.cny_to_points_rate"
                :min="1"
                :max="100"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSystemConfig" :loading="savingConfig">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 风格模板管理 -->
        <div v-if="activeMenu === 'style-templates'" class="templates-section">
          <h2>风格模板管理</h2>
          <div class="toolbar">
            <el-button type="primary" @click="showTemplateDialog = true">
              <el-icon><plus /></el-icon>
              新增风格
            </el-button>
          </div>
          
          <el-table :data="styleTemplates" v-loading="loadingTemplates">
            <el-table-column prop="name" label="风格名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="缩略图">
              <template #default="scope">
                <img
                  v-if="scope.row.thumbnail_url"
                  :src="scope.row.thumbnail_url"
                  alt="缩略图"
                  style="width: 60px; height: 60px; object-fit: cover;"
                >
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态">
              <template #default="scope">
                <el-switch
                  v-model="scope.row.is_active"
                  @change="toggleTemplateStatus(scope.row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button
                  type="primary"
                  size="small"
                  @click="editTemplate(scope.row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="deleteTemplate(scope.row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- API通道管理 -->
        <div v-if="activeMenu === 'api-channels'" class="channels-section">
          <h2>API通道管理</h2>
          <div class="toolbar">
            <el-button type="primary" @click="showChannelDialog = true">
              <el-icon><plus /></el-icon>
              新增通道
            </el-button>
          </div>
          
          <div class="channels-grid">
            <div
              v-for="channel in apiChannels"
              :key="channel.id"
              class="channel-card"
              :class="{ 'unhealthy': !channel.is_healthy }"
            >
              <div class="channel-header">
                <h4>{{ channel.name }}</h4>
                <el-tag :type="channel.is_healthy ? 'success' : 'danger'">
                  {{ channel.is_healthy ? '健康' : '异常' }}
                </el-tag>
              </div>
              <div class="channel-info">
                <div class="info-item">
                  <span>基础URL：</span>
                  <span class="info-value">{{ channel.base_url }}</span>
                </div>
                <div class="info-item">
                  <span>延迟：</span>
                  <span class="info-value">{{ channel.latency_ms || '-' }}ms</span>
                </div>
                <div class="info-item">
                  <span>最后检查：</span>
                  <span class="info-value">{{ formatDate(channel.last_checked_at) || '从未' }}</span>
                </div>
              </div>
              <div class="channel-models">
                <h5>可用模型</h5>
                <div class="models-list">
                  <el-tag
                    v-for="model in channel.models"
                    :key="model.id"
                    :type="model.is_available ? 'info' : 'warning'"
                    size="small"
                  >
                    {{ model.model_name }}
                  </el-tag>
                </div>
              </div>
              <div class="channel-actions">
                <el-switch
                  v-model="channel.is_active"
                  @change="toggleChannelStatus(channel)"
                />
                <el-button
                  type="primary"
                  size="small"
                  @click="testChannel(channel)"
                  :loading="testingChannel === channel.id"
                >
                  测试连接
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  @click="editChannel(channel)"
                >
                  编辑
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>

    <!-- 调整积分对话框 -->
    <el-dialog v-model="showPointsDialog" title="调整用户积分" width="400px">
      <el-form :model="pointsForm">
        <el-form-item label="当前积分">
          <span>{{ currentUser?.points || 0 }}</span>
        </el-form-item>
        <el-form-item label="调整数量">
          <el-input-number
            v-model="pointsForm.adjustment"
            :step="10"
          />
          <span class="form-tip">正数为增加，负数为扣除</span>
        </el-form-item>
        <el-form-item label="调整原因">
          <el-input
            v-model="pointsForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入调整原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPointsDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAdjustPoints">确认</el-button>
      </template>
    </el-dialog>

    <!-- 风格模板编辑对话框 -->
    <el-dialog 
      v-model="showTemplateDialog" 
      :title="editingTemplate ? '编辑风格模板' : '新增风格模板'" 
      width="600px"
    >
      <el-form :model="templateForm" label-width="100px">
        <el-form-item label="风格名称" required>
          <el-input v-model="templateForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="templateForm.description"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        <el-form-item label="缩略图URL">
          <el-input v-model="templateForm.thumbnail_url" />
        </el-form-item>
        <el-form-item label="提示词指令" required>
          <el-input