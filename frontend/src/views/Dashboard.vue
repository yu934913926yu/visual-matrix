<template>
  <div class="dashboard">
    <div class="workspace-container">
      <h2>AI图片生成工作台</h2>
      
      <!-- 图片上传区域 -->
      <el-card class="upload-card" v-if="!uploadedImage">
        <el-upload
          class="upload-dragger"
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleFileSelect"
          accept="image/*"
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
              一键智能生成
            </el-button>
            <el-button
              size="large"
              @click="showCustomOptions = true"
            >
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
                <div class="style-grid">
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

      <!-- 分析结果和微调 -->
      <el-card v-if="analysisResult">
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
            <span>消耗积分：{{ calculateCost }} 分</span>
          </div>
          
          <el-button
            type="primary"
            size="large"
            @click="startGeneration"
            :loading="generating"
            :disabled="userPoints < calculateCost"
          >
            生成图片 (消耗 {{ calculateCost }} 积分)
          </el-button>
        </div>
      </el-card>

      <!-- 生成结果 -->
      <el-card v-if="generatedImages.length > 0">
        <h3>生成结果</h3>
        <div class="results-gallery">
          <div
            v-for="(image, index) in generatedImages"
            :key="index"
            class="result-item"
          >
            <img :src="image.url" :alt="`生成图片 ${index + 1}`" />
            <div class="result-actions">
              <el-button size="small" @click="editImage(image)">
                添加文字/LOGO
              </el-button>
              <el-button size="small" type="success" @click="downloadImage(image)">
                下载
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图片编辑器对话框 -->
    <el-dialog v-model="showEditor" title="图片编辑器" width="80%" fullscreen>
      <div id="canvas-container" style="text-align: center;">
        <canvas id="fabric-canvas" width="800" height="600"></canvas>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditor = false">取消</el-button>
          <el-button type="primary" @click="finalizeImage">完成并下载</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'Dashboard',
  components: {
    UploadFilled
  },
  setup() {
    const uploadedImage = ref('')
    const analysisResult = ref('')
    const finalPrompt = ref('')
    const customPrompt = ref('')
    const selectedStyleId = ref(null)
    const quantity = ref(1)
    const generatedImages = ref([])
    const styleTemplates = ref([])
    
    const showCustomOptions = ref(false)
    const showEditor = ref(false)
    const analyzing = ref(false)
    const generating = ref(false)
    
    const userPoints = ref(50) // 这应该从用户信息中获取
    
    const calculateCost = computed(() => {
      const baseCost = 10 // 基础积分成本
      const membershipDiscount = 1 // 会员折扣，这里需要根据实际会员状态计算
      return quantity.value * baseCost * membershipDiscount
    })
    
    const handleFileSelect = (file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        uploadedImage.value = e.target.result
      }
      reader.readAsDataURL(file.raw)
    }
    
    const startQuickGeneration = async () => {
      analyzing.value = true
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 2000))
        analysisResult.value = true
        finalPrompt.value = "一个精美的产品展示场景，背景简洁优雅，光线柔和自然，突出产品的质感和特色..."
      } catch (error) {
        ElMessage.error('分析失败，请重试')
      } finally {
        analyzing.value = false
      }
    }
    
    const startCustomGeneration = async () => {
      if (!customPrompt.value && !selectedStyleId.value) {
        ElMessage.warning('请输入自定义需求或选择风格模板')
        return
      }
      
      analyzing.value = true
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 2000))
        analysisResult.value = true
        finalPrompt.value = `基于您的需求"${customPrompt.value}"，结合选择的风格，为您生成以下创意脚本...`
      } catch (error) {
        ElMessage.error('分析失败，请重试')
      } finally {
        analyzing.value = false
      }
    }
    
    const startGeneration = async () => {
      if (userPoints.value < calculateCost.value) {
        ElMessage.error('积分不足，请先充值')
        return
      }
      
      generating.value = true
      try {
        // 模拟生成图片
        await new Promise(resolve => setTimeout(resolve, 3000))
        
        const mockImages = []
        for (let i = 0; i < quantity.value; i++) {
          mockImages.push({
            id: Date.now() + i,
            url: `https://picsum.photos/400/300?random=${Date.now() + i}`
          })
        }
        
        generatedImages.value = mockImages
        userPoints.value -= calculateCost.value
        
        ElMessage.success(`成功生成${quantity.value}张图片！`)
      } catch (error) {
        ElMessage.error('生成失败，请重试')
      } finally {
        generating.value = false
      }
    }
    
    const editImage = (image) => {
      showEditor.value = true
      // 这里应该初始化Fabric.js编辑器
    }
    
    const downloadImage = (image) => {
      // 下载图片逻辑
      const link = document.createElement('a')
      link.href = image.url
      link.download = `visual-matrix-${image.id}.jpg`
      link.click()
    }
    
    const finalizeImage = () => {
      // 完成编辑并下载
      showEditor.value = false
      ElMessage.success('图片编辑完成！')
    }
    
    onMounted(() => {
      // 加载风格模板
      styleTemplates.value = [
        { id: 1, name: '模特佩戴', thumbnail_url: 'https://picsum.photos/100/100?random=1' },
        { id: 2, name: '自然场景', thumbnail_url: 'https://picsum.photos/100/100?random=2' },
        { id: 3, name: '商务风格', thumbnail_url: 'https://picsum.photos/100/100?random=3' },
        { id: 4, name: '时尚潮流', thumbnail_url: 'https://picsum.photos/100/100?random=4' }
      ]
    })
    
    return {
      uploadedImage,
      analysisResult,
      finalPrompt,
      customPrompt,
      selectedStyleId,
      quantity,
      generatedImages,
      styleTemplates,
      showCustomOptions,
      showEditor,
      analyzing,
      generating,
      userPoints,
      calculateCost,
      handleFileSelect,
      startQuickGeneration,
      startCustomGeneration,
      startGeneration,
      editImage,
      downloadImage,
      finalizeImage
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.workspace-container h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.upload-card {
  margin-bottom: 20px;
}

.upload-dragger {
  width: 100%;
}

.image-preview {
  text-align: center;
  margin-bottom: 20px;
}

.image-preview img {
  max-width: 300px;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.generation-options {
  text-align: center;
}

.option-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-top: 20px;
}

.custom-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin: 20px 0;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.style-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.style-card:hover,
.style-card.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.style-card img {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  display: block;
  margin: 0 auto 8px;
}

.custom-actions {
  text-align: center;
  margin-top: 20px;
}

.analysis-result {
  margin: 20px 0;
}

.generation-controls {
  margin-top: 30px;
}

.quantity-selector {
  margin: 20px 0;
  display: flex;
  align-items: center;
  gap: 15px;
}

.cost-display {
  margin: 15px 0;
  font-size: 16px;
  font-weight: bold;
  color: #409eff;
}

.results-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.result-item {
  text-align: center;
}

.result-item img {
  width: 100%;
  max-width: 250px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.result-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  justify-content: center;
}
</style>