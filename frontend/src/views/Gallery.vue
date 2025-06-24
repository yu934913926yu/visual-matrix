<template>
  <div class="gallery-container">
    <div class="gallery-header">
      <h2>我的作品</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateFolder = true">
          <el-icon><folder-add /></el-icon>
          新建文件夹
        </el-button>
      </div>
    </div>

    <div class="gallery-content">
      <!-- 侧边栏 - 文件夹列表 -->
      <div class="gallery-sidebar">
        <div class="folder-list">
          <div
            class="folder-item"
            :class="{ active: selectedFolder === null }"
            @click="selectedFolder = null"
          >
            <el-icon><files /></el-icon>
            <span>全部作品</span>
            <span class="count">{{ totalTaskCount }}</span>
          </div>
          
          <div class="folder-divider"></div>
          
          <div
            v-for="folder in folders"
            :key="folder.id"
            class="folder-item"
            :class="{ active: selectedFolder === folder.id }"
            @click="selectedFolder = folder.id"
          >
            <el-icon><folder /></el-icon>
            <span>{{ folder.name }}</span>
            <span class="count">{{ folder.task_count }}</span>
            <el-dropdown
              trigger="click"
              @command="handleFolderCommand($event, folder)"
              @click.stop
            >
              <el-icon class="folder-more"><more /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 主内容区 - 作品展示 -->
      <div class="gallery-main">
        <div class="filter-bar">
          <el-select v-model="filterStatus" placeholder="全部状态" clearable>
            <el-option label="全部状态" value="" />
            <el-option label="生成中" value="generating" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
          
          <el-select v-model="sortBy" placeholder="排序方式">
            <el-option label="创建时间倒序" value="created_desc" />
            <el-option label="创建时间正序" value="created_asc" />
          </el-select>
        </div>

        <div class="tasks-grid" v-loading="loadingTasks">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="task-card"
          >
            <div class="task-header">
              <el-tag
                :type="getStatusType(task.status)"
                size="small"
              >
                {{ getStatusText(task.status) }}
              </el-tag>
              <span class="task-date">{{ formatDate(task.created_at) }}</span>
            </div>
            
            <div class="task-images">
              <div
                v-for="(image, index) in task.generated_images"
                :key="image.id"
                class="image-item"
                @click="viewImage(image)"
              >
                <img :src="image.image_url" :alt="`作品${index + 1}`">
                <div class="image-overlay">
                  <el-button-group>
                    <el-button size="small" type="primary" icon="View" />
                    <el-button 
                      size="small" 
                      icon="Download"
                      @click.stop="downloadImage(image)"
                    />
                  </el-button-group>
                </div>
                <el-tag
                  v-if="image.finalized_image_url"
                  class="edited-tag"
                  type="success"
                  size="small"
                >
                  已编辑
                </el-tag>
              </div>
              
              <div
                v-if="task.quantity_requested > task.generated_images.length"
                class="image-placeholder"
              >
                <el-icon><picture /></el-icon>
                <span>生成中...</span>
              </div>
            </div>
            
            <div class="task-footer">
              <div class="task-info">
                <span>生成 {{ task.quantity_succeeded }}/{{ task.quantity_requested }} 张</span>
                <span>消耗 {{ task.total_cost_points }} 积分</span>
              </div>
              <el-dropdown @command="handleTaskCommand($event, task)">
                <el-button size="small" text>
                  操作
                  <el-icon><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="move">移动到文件夹</el-dropdown-item>
                    <el-dropdown-item command="regenerate" v-if="task.status === 'failed'">
                      重新生成
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>

        <el-pagination
          v-if="pagination.total > 0"
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadTasks"
        />
      </div>
    </div>

    <!-- 创建文件夹对话框 -->
    <el-dialog v-model="showCreateFolder" title="新建文件夹" width="400px">
      <el-form :model="folderForm">
        <el-form-item label="文件夹名称" required>
          <el-input
            v-model="folderForm.name"
            placeholder="请输入文件夹名称"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateFolder = false">取消</el-button>
        <el-button type="primary" @click="createFolder">创建</el-button>
      </template>
    </el-dialog>

    <!-- 移动到文件夹对话框 -->
    <el-dialog v-model="showMoveDialog" title="移动到文件夹" width="400px">
      <el-radio-group v-model="targetFolderId">
        <el-radio :label="null">
          <el-icon><files /></el-icon>
          未分类
        </el-radio>
        <el-radio
          v-for="folder in folders"
          :key="folder.id"
          :label="folder.id"
        >
          <el-icon><folder /></el-icon>
          {{ folder.name }}
        </el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="showMoveDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmMove">确定</el-button>
      </template>
    </el-dialog>

    <!-- 图片查看器 -->
    <el-dialog
      v-model="showImageViewer"
      :title="`作品详情`"
      width="80%"
      class="image-viewer-dialog"
    >
      <div class="image-viewer">
        <img :src="currentImage?.finalized_image_url || currentImage?.image_url" alt="作品">
        <div class="image-actions">
          <el-button type="primary" @click="downloadImage(currentImage)">
            <el-icon><download /></el-icon>
            下载原图
          </el-button>
          <el-button v-if="currentImage?.finalized_image_url" @click="downloadFinalImage(currentImage)">
            <el-icon><download /></el-icon>
            下载编辑版
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  FolderAdd,
  Files,
  Folder,
  More,
  Picture,
  ArrowDown,
  Download,
  View
} from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'Gallery',
  components: {
    FolderAdd,
    Files,
    Folder,
    More,
    Picture,
    ArrowDown,
    Download,
    View
  },
  setup() {
    const folders = ref([])
    const tasks = ref([])
    const selectedFolder = ref(null)
    const filterStatus = ref('')
    const sortBy = ref('created_desc')
    const loadingTasks = ref(false)
    const showCreateFolder = ref(false)
    const showMoveDialog = ref(false)
    const showImageViewer = ref(false)
    const currentTask = ref(null)
    const currentImage = ref(null)
    const targetFolderId = ref(null)
    
    const folderForm = reactive({
      name: ''
    })
    
    const pagination = reactive({
      page: 1,
      per_page: 12,
      total: 0
    })
    
    const totalTaskCount = computed(() => {
      return folders.value.reduce((sum, folder) => sum + folder.task_count, 0)
    })
    
    // 加载文件夹列表
    const loadFolders = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/projects', {
          headers: { Authorization: `Bearer ${token}` }
        })
        folders.value = response.data.folders
      } catch (error) {
        console.error('加载文件夹失败:', error)
      }
    }
    
    // 加载任务列表
    const loadTasks = async () => {
      try {
        loadingTasks.value = true
        const token = localStorage.getItem('token')
        const params = {
          page: pagination.page,
          per_page: pagination.per_page
        }
        
        if (selectedFolder.value) {
          params.project_id = selectedFolder.value
        }
        
        if (filterStatus.value) {
          params.status = filterStatus.value
        }
        
        const response = await axios.get('/api/my-tasks', {
          params,
          headers: { Authorization: `Bearer ${token}` }
        })
        
        tasks.value = response.data.tasks
        Object.assign(pagination, response.data.pagination)
      } catch (error) {
        ElMessage.error('加载作品失败')
      } finally {
        loadingTasks.value = false
      }
    }
    
    // 创建文件夹
    const createFolder = async () => {
      if (!folderForm.name) {
        ElMessage.warning('请输入文件夹名称')
        return
      }
      
      try {
        const token = localStorage.getItem('token')
        await axios.post('/api/projects', {
          name: folderForm.name
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        ElMessage.success('文件夹创建成功')
        showCreateFolder.value = false
        folderForm.name = ''
        loadFolders()
      } catch (error) {
        ElMessage.error('创建文件夹失败')
      }
    }
    
    // 处理文件夹操作
    const handleFolderCommand = async (command, folder) => {
      if (command === 'rename') {
        try {
          const { value } = await ElMessageBox.prompt('重命名文件夹', '提示', {
            inputValue: folder.name,
            inputPattern: /.+/,
            inputErrorMessage: '文件夹名称不能为空'
          })
          
          // 这里应该调用重命名API
          ElMessage.info('重命名功能开发中...')
        } catch {
          // 用户取消
        }
      } else if (command === 'delete') {
        try {
          await ElMessageBox.confirm('确定删除该文件夹吗？文件夹内的作品将移至未分类', '提示', {
            type: 'warning'
          })
          
          // 这里应该调用删除API
          ElMessage.info('删除功能开发中...')
        } catch {
          // 用户取消
        }
      }
    }
    
    // 处理任务操作
    const handleTaskCommand = (command, task) => {
      currentTask.value = task
      
      if (command === 'move') {
        targetFolderId.value = task.project_id
        showMoveDialog.value = true
      } else if (command === 'regenerate') {
        regenerateTask(task)
      } else if (command === 'delete') {
        deleteTask(task)
      }
    }
    
    // 确认移动
    const confirmMove = async () => {
      try {
        const token = localStorage.getItem('token')
        await axios.post(`/api/tasks/${currentTask.value.id}/move-to-project`, {
          project_id: targetFolderId.value
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        ElMessage.success('移动成功')
        showMoveDialog.value = false
        loadTasks()
        loadFolders()
      } catch (error) {
        ElMessage.error('移动失败')
      }
    }
    
    // 重新生成任务
    const regenerateTask = async (task) => {
      try {
        await ElMessageBox.confirm('确定要重新生成吗？将消耗相应积分', '提示', {
          type: 'warning'
        })
        
        // 这里应该调用重新生成API
        ElMessage.info('重新生成功能开发中...')
      } catch {
        // 用户取消
      }
    }
    
    // 删除任务
    const deleteTask = async (task) => {
      try {
        await ElMessageBox.confirm('确定删除该任务吗？此操作不可恢复', '提示', {
          type: 'warning'
        })
        
        // 这里应该调用删除API
        ElMessage.info('删除功能开发中...')
      } catch {
        // 用户取消
      }
    }
    
    // 查看图片
    const viewImage = (image) => {
      currentImage.value = image
      showImageViewer.value = true
    }
    
    // 下载图片
    const downloadImage = (image) => {
      const link = document.createElement('a')
      link.href = image.image_url
      link.download = `visual-matrix-${image.id}.jpg`
      link.click()
    }
    
    // 下载编辑版图片
    const downloadFinalImage = (image) => {
      const link = document.createElement('a')
      link.href = image.finalized_image_url
      link.download = `visual-matrix-final-${image.id}.jpg`
      link.click()
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN')
    }
    
    // 获取状态类型
    const getStatusType = (status) => {
      const typeMap = {
        'pending': 'info',
        'analyzing': 'warning',
        'generating': 'warning',
        'completed': 'success',
        'failed': 'danger'
      }
      return typeMap[status] || 'info'
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      const textMap = {
        'pending': '等待中',
        'analyzing': '分析中',
        'generating': '生成中',
        'completed': '已完成',
        'failed': '失败'
      }
      return textMap[status] || status
    }
    
    // 监听筛选条件变化
    watch([selectedFolder, filterStatus, sortBy], () => {
      pagination.page = 1
      loadTasks()
    })
    
    onMounted(() => {
      loadFolders()
      loadTasks()
    })
    
    return {
      folders,
      tasks,
      selectedFolder,
      filterStatus,
      sortBy,
      loadingTasks,
      showCreateFolder,
      showMoveDialog,
      showImageViewer,
      currentImage,
      targetFolderId,
      folderForm,
      pagination,
      totalTaskCount,
      createFolder,
      handleFolderCommand,
      handleTaskCommand,
      confirmMove,
      viewImage,
      downloadImage,
      downloadFinalImage,
      formatDate,
      getStatusType,
      getStatusText
    }
  }
}
</script>

<style scoped>
.gallery-container {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.gallery-header h2 {
  margin: 0;
}

.gallery-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 侧边栏 */
.gallery-sidebar {
  width: 250px;
  background: white;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}

.folder-list {
  padding: 10px;
}

.folder-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.folder-item:hover {
  background: #f5f7fa;
}

.folder-item.active {
  background: #ecf5ff;
  color: #409eff;
}

.folder-item .el-icon {
  margin-right: 10px;
  font-size: 18px;
}

.folder-item span:nth-child(2) {
  flex: 1;
}

.folder-item .count {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.folder-item .folder-more {
  opacity: 0;
  transition: opacity 0.3s;
}

.folder-item:hover .folder-more {
  opacity: 1;
}

.folder-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 10px 0;
}

/* 主内容区 */
.gallery-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f5f7fa;
}

.filter-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

/* 任务网格 */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.task-card {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.task-date {
  font-size: 12px;
  color: #909399;
}

/* 图片展示 */
.task-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
  margin-bottom: 15px;
}

.image-item {
  position: relative;
  padding-bottom: 100%;
  overflow: hidden;
  border-radius: 4px;
  cursor: pointer;
}

.image-item img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.edited-tag {
  position: absolute;
  top: 5px;
  right: 5px;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border: 2px dashed #dcdfe6;
  border-radius: 4px;
  color: #909399;
  font-size: 12px;
  gap: 5px;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}

.task-info {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #909399;
}

/* 图片查看器 */
.image-viewer-dialog .el-dialog__body {
  padding: 0;
}

.image-viewer {
  background: #000;
  text-align: center;
  position: relative;
}

.image-viewer img {
  max-width: 100%;
  max-height: 80vh;
}

.image-actions {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
}

/* 单选组样式 */
.el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.el-radio {
  display: flex;
  align-items: center;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  transition: all 0.3s;
}

.el-radio:hover {
  background: #f5f7fa;
}

.el-radio__input.is-checked + .el-radio__label {
  color: #409eff;
}
</style>