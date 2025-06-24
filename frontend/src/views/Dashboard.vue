<template>
  <div class="dashboard">
    <div class="workspace-container">
      <h2>AI图片生成工作台</h2>
      
      <!-- 用户信息和积分显示 -->
      <el-card class="user-info-card" v-if="userInfo">
        <div class="user-stats">
          <div class="stat-item">
            <span class="label">当前积分：</span>
            <span class="value">{{ userInfo.points }}</span>
          </div>
          <div class="stat-item" v-if="userInfo.membership_tier_id">
            <span class="label">会员状态：</span>
            <span class="value member">VIP会员</span>
            <el-tag type="success" size="small">6折优惠</el-tag>
          </div>
        </div>
      </el-card>
      
      <!-- 图片上传区域 -->
      <el-card class="upload-card" v-if="!uploadedImage">
        <el-upload
          class="upload-dragger"
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleFileSelect"
          accept="image/*"
          :show-file-list="false"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将图片拖拽到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 jpg/png/gif 文件，且不超过 10MB
            </div>
          </template>
        </el-upload>
      </el-card>

      <!-- 图片预览和创意选择 -->
      <el-card v-if="uploadedImage && !analysisResult">
        <div class="image-preview">
          <img :src="uploadedImage" alt="上传的图片" />
          <el-button @click="resetUpload" type="text" class="reset-btn">
            <el-icon><refresh /></el-icon>
            重新上传
          </el-button>
        </div>
        
        <div class="generation-options">
          <h3>选择生成方式</h3>
          <div class="option-buttons">
            <el-button
              type="primary"
              size="large"
              @click="startQuickGeneration"
              :loading="analyzing"
            >
              <el-icon><magic-stick /></el-icon>
              一键智能生成
            </el-button>
            <el-button
              size="large"
              @click="showCustomOptions = true"
            >
              <el-icon><setting /></el-icon>
              按我的需求生成
            </el-button>
          </div>
        </div>

        <!-- 自定义需求面板 -->
        <el-collapse v-model="showCustomOptions" v-if="showCustomOptions">
          <el-collapse-item name="custom">
            <template #title>
              <h4>自定义生成需求</h4>
            </template>
            <div class="custom-options">
              <div class="custom-left">
                <h5>描述您的具体想法</h5>
                <el-input
                  v-model="customPrompt"
                  type="textarea"
                  :rows="4"
                  placeholder="请在此输入您的具体想法、场景或关键词..."
                />
              </div>
              <div class="custom-right">
                <h5>官方风格库</h5>
                <div class="style-grid" v-loading="loadingStyles">
                  <div
                    v-for="style in styleTemplates"
                    :key="style.id"
                    class="style-card"
                    :class="{ active: selectedStyleId === style.id }"
                    @click="selectedStyleId = style.id"
                  >
                    <img :src="style.thumbnail_url" :alt="style.name" />
                    <span>{{ style.name }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="custom-actions">
              <el-button
                type="primary"
                @click="startCustomGeneration"
                :loading="analyzing"
              >
                生成创意脚本
              </el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 分析进度 -->
      <el-card v-if="analyzing">
        <div class="analysis-progress">
          <el-icon class="rotating"><loading /></el-icon>
          <h3>AI正在分析您的图片...</h3>
          <p>这通常需要10-30秒，请稍候</p>
        </div>
      </el-card>

      <!-- 分析结果和微调 -->
      <el-card v-if="analysisResult && !generating && generatedImages.length === 0">
        <h3>AI分析结果</h3>
        <div class="analysis-result">
          <el-input
            v-model="finalPrompt"
            type="textarea"
            :rows="6"
            placeholder="AI生成的提示词将在这里显示..."
          />
        </div>
        
        <div class="generation-controls">
          <h4>生成设置</h4>
          <div class="quantity-selector">
            <span>生成数量：</span>
            <el-radio-group v-model="quantity">
              <el-radio :label="1">1张</el-radio>
              <el-radio :label="2">2张</el-radio>
              <el-radio :label="3">3张</el-radio>
              <el-radio :label="4">4张</el-radio>
            </el-radio-group>
          </div>
          
          <div class="cost-display">
            <div class="cost-breakdown">
              <span>基础费用：{{ baseCost * quantity }} 积分</span>
              <span v-if="memberDiscount < 1" class="discount">
                会员折扣：-{{ Math.round((1 - memberDiscount) * 100) }}%
              </span>
              <span class="final-cost">总计：{{ calculateCost }} 积分</span>
            </div>
          </div>
          
          <el-button
            type="primary"
            size="large"
            @click="startGeneration"
            :loading="generating"
            :disabled="userInfo && userInfo.points < calculateCost"
          >
            <el-icon><picture /></el-icon>
            生成图片 (消耗 {{ calculateCost }} 积分)
          </el-button>
          
          <div v-if="userInfo && userInfo.points < calculateCost" class="insufficient-points">
            <el-icon><warning /></el-icon>
            积分不足，<el-button type="text" @click="$router.push('/recharge')">立即充值</el-button>
          </div>
        </div>
      </el-card>

      <!-- 生成进度 -->
      <el-card v-if="generating">
        <div class="generation-progress">
          <h3>AI正在为您生成图片...</h3>
          <el-progress 
            :percentage="generationProgress" 
            :status="generationProgress === 100 ? 'success' : null"
          />
          <p>已完成 {{ completedImages }} / {{ quantity }} 张</p>
          
          <!-- 实时显示已生成的图片 -->
          <div class="progress-gallery" v-if="progressImages.length > 0">
            <div v-for="(image, index) in progressImages" :key="index" class="progress-item">
              <img :src="image.url" :alt="`生成图片 ${index + 1}`" />
            </div>
          </div>
        </div>
      </el-card>

      <!-- 生成结果 -->
      <el-card v-if="generatedImages.length > 0 && !generating">
        <div class="results-header">
          <h3>生成结果</h3>
          <el-button-group>
            <el-button @click="downloadAll">
              <el-icon><download /></el-icon>
              下载全部
            </el-button>
            <el-button @click="showProjectDialog = true">
              <el-icon><folder /></el-icon>
              保存到项目
            </el-button>
          </el-button-group>
        </div>
        
        <div class="results-gallery">
          <div
            v-for="(image, index) in generatedImages"
            :key="index"
            class="result-item"
          >
            <div class="image-container">
              <img :src="image.url" :alt="`生成图片 ${index + 1}`" />
              <div class="image-overlay">
                <el-button-group>
                  <el-button size="small" @click="editImage(image)">
                    <el-icon><edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button size="small" type="success" @click="downloadImage(image)">
                    <el-icon><download /></el-icon>
                    下载
                  </el-button>
                </el-button-group>
              </div>
            </div>
            <div class="result-info">
              <p>图片 {{ index + 1 }}</p>
              <el-rate v-model="image.rating" @change="rateImage(image)" />
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图片编辑器对话框 -->
    <el-dialog 
      v-model="showEditor" 
      title="图片编辑器" 
      width="90%" 
      :fullscreen="editorFullscreen"
      class="editor-dialog"
    >
      <div class="editor-container">
        <div class="editor-toolbar">
          <el-button-group>
            <el-button @click="addText">
              <el-icon><edit /></el-icon>
              添加文字
            </el-button>
            <el-button @click="uploadLogo">
              <el-icon><picture /></el-icon>
              上传LOGO
            </el-button>
            <el-button @click="addShape">
              <el-icon><crop /></el-icon>
              添加形状
            </el-button>
          </el-button-group>
          
          <el-button @click="editorFullscreen = !editorFullscreen">
            <el-icon><full-screen /></el-icon>
            {{ editorFullscreen ? '退出全屏' : '全屏' }}
          </el-button>
        </div>
        
        <div class="canvas-container">
          <canvas id="fabric-canvas" width="800" height="600"></canvas>
        </div>
        
        <div class="editor-properties" v-if="selectedObject">
          <h4>属性面板</h4>
          <div v-if="selectedObject.type === 'textbox'">
            <el-form-item label="文字内容">
              <el-input v-model="selectedObject.text" @input="updateObjectProperty('text', selectedObject.text)" />
            </el-form-item>
            <el-form-item label="字体大小">
              <el-slider v-model="selectedObject.fontSize" :min="12" :max="100" @input="updateObjectProperty('fontSize', selectedObject.fontSize)" />
            </el-form-item>
            <el-form-item label="颜色">
              <el-color-picker v-model="selectedObject.fill" @change="updateObjectProperty('fill', selectedObject.fill)" />
            </el-form-item>
          </div>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditor = false">取消</el-button>
          <el-button type="primary" @click="finalizeImage" :loading="finalizing">
            完成并下载
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 保存到项目对话框 -->
    <el-dialog v-model="showProjectDialog" title="保存到项目" width="400px">
      <el-form>
        <el-form-item label="选择项目">
          <el-select v-model="selectedProjectId" placeholder="选择一个项目文件夹">
            <el-option
              v-for="project in userProjects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="createNewProject" type="text">
            <el-icon><plus /></el-icon>
            创建新项目
          </el-button>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showProjectDialog = false">取消</el-button>
          <el-button type="primary" @click="saveToProject">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UploadFilled, 
  MagicStick, 
  Setting, 
  Loading, 
  Picture, 
  Warning,
  Download,
  Folder,
  Edit,
  Refresh,
  FullScreen,
  Crop,
  Plus
} from '@element-plus/icons-vue'
import axios from 'axios'
import { fabric } from 'fabric'
import io from 'socket.io-client'

export default {
  name: 'Dashboard',
  components: {
    UploadFilled,
    MagicStick,
    Setting,
    Loading,
    Picture,
    Warning,
    Download,
    Folder,
    Edit,
    Refresh,
    FullScreen,
    Crop,
    Plus
  },
  setup() {
    const uploadedImage = ref('')
    const analysisResult = ref(false)
    const finalPrompt = ref('')
    const customPrompt = ref('')
    const selectedStyleId = ref(null)
    const quantity = ref(1)
    const generatedImages = ref([])
    const progressImages = ref([])
    const styleTemplates = ref([])
    const userInfo = ref(null)
    const userProjects = ref([])
    
    const showCustomOptions = ref('')
    const showEditor = ref(false)
    const showProjectDialog = ref(false)
    const editorFullscreen = ref(false)
    
    const analyzing = ref(false)
    const generating = ref(false)
    const finalizing = ref(false)
    const loadingStyles = ref(false)
    
    const completedImages = ref(0)
    const currentTask = ref(null)
    const selectedProjectId = ref(null)
    
    // WebSocket相关
    const socket = ref(null)
    
    // Fabric.js相关
    const fabricCanvas = ref(null)
    const selectedObject = ref(null)
    
    const baseCost = ref(10)
    const memberDiscount = ref(1)
    
    const calculateCost = computed(() => {
      return Math.ceil(baseCost.value * quantity.value * memberDiscount.value)
    })
    
    const generationProgress = computed(() => {
      if (quantity.value === 0) return 0
      return Math.round((completedImages.value / quantity.value) * 100)
    })
    
    // 初始化WebSocket连接
    const initWebSocket = () => {
      const token = localStorage.getItem('token')
      if (!token) return
      
      socket.value = io('http://localhost:5000', {
        auth: { token }
      })
      
      socket.value.on('connect', () => {
        console.log('WebSocket connected')
        if (userInfo.value) {
          socket.value.emit('join_user_room', { user_id: userInfo.value.id })
        }
      })
      
      socket.value.on('analysis_complete', (data) => {
        analyzing.value = false
        analysisResult.value = true
        finalPrompt.value = data.prompt
        ElMessage.success('图片分析完成！')
      })
      
      socket.value.on('analysis_failed', (data) => {
        analyzing.value = false
        ElMessage.error(`分析失败：${data.error}`)
      })
      
      socket.value.on('generation_started', (data) => {
        generating.value = true
        completedImages.value = 0
        progressImages.value = []
      })
      
      socket.value.on('generation_progress', (data) => {
        completedImages.value = data.completed
        progressImages.value.push({ url: data.image_url })
      })
      
      socket.value.on('generation_complete', (data) => {
        generating.value = false
        generatedImages.value = data.images.map(img => ({
          ...img,
          rating: 0
        }))
        ElMessage.success(`成功生成${data.images.length}张图片！`)
      })
      
      socket.value.on('generation_failed', (data) => {
        generating.value = false
        ElMessage.error(`生成失败：${data.error}`)
      })
      
      socket.value.on('payment_success', (data) => {
        ElMessage.success('充值成功！')
        loadUserInfo() // 刷新用户信息
      })
    }
    
    const loadUserInfo = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/auth/profile', {
          headers: { Authorization: `Bearer ${token}` }
        })
        userInfo.value = response.data.user
        
        // 计算会员折扣
        if (userInfo.value.membership_tier_id && userInfo.value.membership_expires_at) {
          const expiresAt = new Date(userInfo.value.membership_expires_at)
          if (expiresAt > new Date()) {
            memberDiscount.value = 0.6 // 6折优惠
          }
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    }
    
    const loadStyleTemplates = async () => {
      try {
        loadingStyles.value = true
        const response = await axios.get('/api/style-templates')
        styleTemplates.value = response.data.templates
      } catch (error) {
        console.error('获取风格模板失败:', error)
      } finally {
        loadingStyles.value = false
      }
    }
    
    const loadUserProjects = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/projects', {
          headers: { Authorization: `Bearer ${token}` }
        })
        userProjects.value = response.data.folders
      } catch (error) {
        console.error('获取项目列表失败:', error)
      }
    }
    
    const handleFileSelect = (file) => {
      if (file.size > 10 * 1024 * 1024) {
        ElMessage.error('文件大小不能超过10MB')
        return
      }
      
      const reader = new FileReader()
      reader.onload = (e) => {
        uploadedImage.value = e.target.result
      }
      reader.readAsDataURL(file.raw)
    }
    
    const resetUpload = () => {
      uploadedImage.value = ''
      analysisResult.value = false
      finalPrompt.value = ''
      customPrompt.value = ''
      selectedStyleId.value = null
      generatedImages.value = []
      progressImages.value = []
      showCustomOptions.value = ''
    }
    
    const startQuickGeneration = async () => {
      if (!uploadedImage.value) return
      
      analyzing.value = true
      
      try {
        // 将base64转换为文件
        const blob = await fetch(uploadedImage.value).then(r => r.blob())
        const formData = new FormData()
        formData.append('image', blob, 'upload.jpg')
        
        const token = localStorage.getItem('token')
        const response = await axios.post('/api/analyze-image', formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        })
        
        currentTask.value = response.data.task_id
        // WebSocket会处理后续的分析完成通知
        
      } catch (error) {
        analyzing.value = false
        ElMessage.error(error.response?.data?.error || '分析失败')
      }
    }
    
    const startCustomGeneration = async () => {
      if (!uploadedImage.value) return
      
      if (!customPrompt.value && !selectedStyleId.value) {
        ElMessage.warning('请输入自定义需求或选择风格模板')
        return
      }
      
      analyzing.value = true
      
      try {
        const blob = await fetch(uploadedImage.value).then(r => r.blob())
        const formData = new FormData()
        formData.append('image', blob, 'upload.jpg')
        formData.append('user_prompt', customPrompt.value)
        if (selectedStyleId.value) {
          formData.append('style_id', selectedStyleId.value)
        }
        
        const token = localStorage.getItem('token')
        const response = await axios.post('/api/analyze-image', formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        })
        
        currentTask.value = response.data.task_id
        
      } catch (error) {
        analyzing.value = false
        ElMessage.error(error.response?.data?.error || '分析失败')
      }
    }
    
    const startGeneration = async () => {
      if (!currentTask.value || !finalPrompt.value) return
      
      try {
        const token = localStorage.getItem('token')
        await axios.post('/api/generate-final-image', {
          task_id: currentTask.value,
          final_prompt: finalPrompt.value,
          quantity: quantity.value
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        // 扣除积分（乐观更新）
        userInfo.value.points -= calculateCost.value
        
      } catch (error) {
        ElMessage.error(error.response?.data?.error || '生成失败')
      }
    }
    
    const editImage = (image) => {
      showEditor.value = true
      
      // 初始化Fabric.js画布
      setTimeout(() => {
        if (!fabricCanvas.value) {
          fabricCanvas.value = new fabric.Canvas('fabric-canvas')
          
          // 加载背景图片
          fabric.Image.fromURL(image.url, (img) => {
            fabricCanvas.value.setBackgroundImage(img, fabricCanvas.value.renderAll.bind(fabricCanvas.value), {
              scaleX: fabricCanvas.value.width / img.width,
              scaleY: fabricCanvas.value.height / img.height
            })
          })
          
          // 监听对象选择
          fabricCanvas.value.on('selection:created', (e) => {
            selectedObject.value = e.selected[0]
          })
          
          fabricCanvas.value.on('selection:updated', (e) => {
            selectedObject.value = e.selected[0]
          })
          
          fabricCanvas.value.on('selection:cleared', () => {
            selectedObject.value = null
          })
        }
      }, 100)
    }
    
    const addText = () => {
      if (!fabricCanvas.value) return
      
      const text = new fabric.Textbox('双击编辑文字', {
        left: 100,
        top: 100,
        fontFamily: 'Arial',
        fontSize: 24,
        fill: '#000000'
      })
      
      fabricCanvas.value.add(text)
      fabricCanvas.value.setActiveObject(text)
      fabricCanvas.value.renderAll()
    }
    
    const uploadLogo = () => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'
      input.onchange = (e) => {
        const file = e.target.files[0]
        if (file) {
          const reader = new FileReader()
          reader.onload = (event) => {
            fabric.Image.fromURL(event.target.result, (img) => {
              img.scale(0.5)
              img.set({
                left: 50,
                top: 50
              })
              fabricCanvas.value.add(img)
              fabricCanvas.value.renderAll()
            })
          }
          reader.readAsDataURL(file)
        }
      }
      input.click()
    }
    
    const addShape = () => {
      ElMessageBox.prompt('选择形状', '添加形状', {
        inputType: 'select',
        inputOptions: [
          { value: 'rect', label: '矩形' },
          { value: 'circle', label: '圆形' },
          { value: 'triangle', label: '三角形' }
        ]
      }).then(({ value }) => {
        let shape
        switch (value) {
          case 'rect':
            shape = new fabric.Rect({
              left: 100,
              top: 100,
              width: 100,
              height: 100,
              fill: 'red'
            })
            break
          case 'circle':
            shape = new fabric.Circle({
              left: 100,
              top: 100,
              radius: 50,
              fill: 'green'
            })
            break
          case 'triangle':
            shape = new fabric.Triangle({
              left: 100,
              top: 100,
              width: 100,
              height: 100,
              fill: 'blue'
            })
            break
        }
        
        if (shape) {
          fabricCanvas.value.add(shape)
          fabricCanvas.value.renderAll()
        }
      })
    }
    
    const updateObjectProperty = (property, value) => {
      if (selectedObject.value && fabricCanvas.value) {
        selectedObject.value.set(property, value)
        fabricCanvas.value.renderAll()
      }
    }
    
    const finalizeImage = async () => {
      if (!fabricCanvas.value) return
      
      finalizing.value = true
      
      try {
        const editorData = fabricCanvas.value.toJSON()
        
        const token = localStorage.getItem('token')
        const response = await axios.post('/api/image/finalize', {
          result_id: currentEditingImage.value.id,
          editor_data: editorData
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        // 下载最终图片
        const link = document.createElement('a')
        link.href = response.data.finalized_image_url
        link.download = `visual-matrix-final-${Date.now()}.jpg`
        link.click()
        
        showEditor.value = false
        ElMessage.success('图片编辑完成并已下载！')
        
      } catch (error) {
        ElMessage.error(error.response?.data?.error || '完成编辑失败')
      } finally {
        finalizing.value = false
      }
    }
    
    const downloadImage = (image) => {
      const link = document.createElement('a')
      link.href = image.url
      link.download = `visual-matrix-${image.id}.jpg`
      link.click()
    }
    
    const downloadAll = () => {
      generatedImages.value.forEach((image, index) => {
        setTimeout(() => {
          downloadImage(image)
        }, index * 500) // 延迟下载避免浏览器阻止
      })
    }
    
    const rateImage = (image) => {
      // 这里可以发送评分到后端
      console.log(`图片 ${image.id} 评分: ${image.rating}`)
    }
    
    const createNewProject = async () => {
      try {
        const { value } = await ElMessageBox.prompt('项目名称', '创建新项目', {
          confirmButtonText: '创建',
          cancelButtonText: '取消'
        })
        
        const token = localStorage.getItem('token')
        const response = await axios.post('/api/projects', {
          name: value
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        await loadUserProjects()
        selectedProjectId.value = response.data.folder_id
        ElMessage.success('项目创建成功')
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('创建项目失败')
        }
      }
    }
    
    const saveToProject = async () => {
      if (!selectedProjectId.value || !currentTask.value) {
        ElMessage.warning('请选择项目')
        return
      }
      
      try {
        const token = localStorage.getItem('token')
        await axios.post(`/api/tasks/${currentTask.value}/move-to-project`, {
          project_id: selectedProjectId.value
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        showProjectDialog.value = false
        ElMessage.success('保存到项目成功')
        
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }
    
    onMounted(() => {
      loadUserInfo()
      loadStyleTemplates()
      loadUserProjects()
      initWebSocket()
    })
    
    onUnmounted(() => {
      if (socket.value) {
        socket.value.disconnect()
      }
      if (fabricCanvas.value) {
        fabricCanvas.value.dispose()
      }
    })
    
    return {
      uploadedImage,
      analysisResult,
      finalPrompt,
      customPrompt,
      selectedStyleId,
      quantity,
      generatedImages,
      progressImages,
      styleTemplates,
      userInfo,
      userProjects,
      showCustomOptions,
      showEditor,
      showProjectDialog,
      editorFullscreen,
      analyzing,
      generating,
      finalizing,
      loadingStyles,
      completedImages,
      selectedProjectId,
      fabricCanvas,
      selectedObject,
      baseCost,
      memberDiscount,
      calculateCost,
      generationProgress,
      handleFileSelect,
      resetUpload,
      startQuickGeneration,
      startCustomGeneration,
      startGeneration,
      editImage,
      addText,
      uploadLogo,
      addShape,
      updateObjectProperty,
      finalizeImage,
      downloadImage,
      downloadAll,
      rateImage,
      createNewProject,
      saveToProject
    }
  }
}
</script>

<style scoped>
/* 原有样式保持不变，新增以下样式 */

.user-info-card {
  margin-bottom: 20px;
}

.user-stats {
  display: flex;
  gap: 30px;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-item .label {
  color: #666;
}

.stat-item .value {
  font-weight: bold;
  color: #409eff;
}

.stat-item .value.member {
  color: #67c23a;
}

.reset-btn {
  position: absolute;
  top: 10px;
  right: 10px;
}

.analysis-progress, .generation-progress {
  text-align: center;
  padding: 40px;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-gallery {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.progress-item img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
}

.cost-breakdown {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.discount {
  color: #67c23a;
  font-size: 14px;
}

.final-cost {
  font-weight: bold;
  font-size: 16px;
  color: #409eff;
}

.insufficient-points {
  margin-top: 10px;
  color: #f56c6c;
  display: flex;
  align-items: center;
  gap: 5px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-item {
  position: relative;
}

.image-container {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.result-item:hover .image-overlay {
  opacity: 1;
}

.result-info {
  padding: 10px;
  text-align: center;
}

.editor-dialog {
  min-height: 80vh;
}

.editor-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

.canvas-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.editor-properties {
  width: 250px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 4px;
  margin-top: 20px;
}
</style>