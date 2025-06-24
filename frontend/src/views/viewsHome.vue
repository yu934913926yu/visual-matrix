<template>
  <div class="home-container">
    <!-- Hero区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          AI驱动的电商视觉创意平台
          <span class="highlight">视觉矩阵</span>
        </h1>
        <p class="hero-subtitle">
          上传产品图，一键生成专业级营销场景图片<br>
          降低90%摄影成本，提升200%视觉营销效果
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" round @click="getStarted">
            立即体验
          </el-button>
          <el-button size="large" round @click="watchDemo">
            观看演示
          </el-button>
        </div>
      </div>
      <div class="hero-image">
        <img src="/static/images/hero-banner.png" alt="视觉矩阵展示">
      </div>
    </section>

    <!-- 特性介绍 -->
    <section class="features-section">
      <div class="section-header">
        <h2>为什么选择视觉矩阵？</h2>
        <p>革命性的AI技术，为您的电商业务赋能</p>
      </div>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="48"><magic-stick /></el-icon>
          </div>
          <h3>智能场景生成</h3>
          <p>AI深度理解产品特性，自动生成最适合的营销场景，无需摄影师和场地</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="48"><timer /></el-icon>
          </div>
          <h3>极速出图</h3>
          <p>从上传到生成仅需30秒，比传统摄影快100倍，抢占市场先机</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="48"><discount /></el-icon>
          </div>
          <h3>成本节省90%</h3>
          <p>无需摄影团队、场地、道具，大幅降低视觉营销成本</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="48"><brush /></el-icon>
          </div>
          <h3>多样化风格</h3>
          <p>海量专业风格模板，满足不同品类和营销场景需求</p>
        </div>
      </div>
    </section>

    <!-- 使用流程 -->
    <section class="process-section">
      <div class="section-header">
        <h2>简单三步，开启视觉营销新纪元</h2>
      </div>
      <div class="process-steps">
        <div class="process-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h3>上传产品图</h3>
            <p>支持各种格式的产品图片，白底图效果最佳</p>
          </div>
        </div>
        <div class="process-arrow">
          <el-icon :size="32"><arrow-right /></el-icon>
        </div>
        <div class="process-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h3>选择风格或自定义</h3>
            <p>使用官方风格库或输入您的创意想法</p>
          </div>
        </div>
        <div class="process-arrow">
          <el-icon :size="32"><arrow-right /></el-icon>
        </div>
        <div class="process-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h3>一键生成&下载</h3>
            <p>AI自动生成专业场景图，支持批量生成和在线编辑</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 价格方案 -->
    <section class="pricing-section">
      <div class="section-header">
        <h2>灵活的定价方案</h2>
        <p>无论您是个人卖家还是大型企业，都有适合的方案</p>
      </div>
      <div class="pricing-cards">
        <div class="pricing-card">
          <h3>积分套餐</h3>
          <p class="price">¥30起</p>
          <ul>
            <li>按需购买，灵活使用</li>
            <li>无时间限制</li>
            <li>适合个人卖家</li>
          </ul>
          <el-button round @click="goToRecharge">查看套餐</el-button>
        </div>
        <div class="pricing-card featured">
          <div class="featured-badge">最受欢迎</div>
          <h3>VIP会员</h3>
          <p class="price">¥29/月</p>
          <ul>
            <li>图片生成6折优惠</li>
            <li>每月赠送500积分</li>
            <li>专属客服支持</li>
            <li>优先体验新功能</li>
          </ul>
          <el-button type="primary" round @click="goToRecharge">立即开通</el-button>
        </div>
        <div class="pricing-card">
          <h3>SVIP会员</h3>
          <p class="price">¥59/月</p>
          <ul>
            <li>图片生成5折优惠</li>
            <li>每月赠送1200积分</li>
            <li>1对1专属客服</li>
            <li>API接口支持</li>
          </ul>
          <el-button round @click="goToRecharge">了解更多</el-button>
        </div>
      </div>
    </section>

    <!-- CTA区域 -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>准备好革新您的视觉营销了吗？</h2>
        <p>新用户注册即送50积分，立即体验AI的魔力</p>
        <el-button type="primary" size="large" round @click="getStarted">
          免费开始
        </el-button>
      </div>
    </section>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  MagicStick, 
  Timer, 
  Discount, 
  Brush, 
  ArrowRight 
} from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    MagicStick,
    Timer,
    Discount,
    Brush,
    ArrowRight
  },
  setup() {
    const router = useRouter()
    
    const getStarted = () => {
      const token = localStorage.getItem('token')
      if (token) {
        router.push('/dashboard')
      } else {
        router.push('/login')
      }
    }
    
    const watchDemo = () => {
      ElMessage.info('演示视频功能开发中...')
    }
    
    const goToRecharge = () => {
      const token = localStorage.getItem('token')
      if (token) {
        router.push('/recharge')
      } else {
        router.push('/login')
      }
    }
    
    return {
      getStarted,
      watchDemo,
      goToRecharge
    }
  }
}
</script>

<style scoped>
.home-container {
  background: #f5f7fa;
}

/* Hero区域 */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 80px 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.hero-content {
  flex: 1;
  max-width: 600px;
}

.hero-title {
  font-size: 48px;
  font-weight: bold;
  line-height: 1.2;
  margin-bottom: 20px;
}

.highlight {
  display: block;
  color: #ffd700;
}

.hero-subtitle {
  font-size: 20px;
  line-height: 1.6;
  margin-bottom: 40px;
  opacity: 0.9;
}

.hero-actions {
  display: flex;
  gap: 20px;
}

.hero-actions .el-button {
  min-width: 150px;
  height: 50px;
  font-size: 18px;
}

.hero-image {
  flex: 1;
  text-align: center;
}

.hero-image img {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* 特性介绍 */
.features-section {
  padding: 80px 40px;
  background: white;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-header h2 {
  font-size: 36px;
  margin-bottom: 15px;
  color: #303133;
}

.section-header p {
  font-size: 18px;
  color: #606266;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  text-align: center;
  padding: 40px 30px;
  border-radius: 12px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  color: white;
  margin-bottom: 20px;
}

.feature-card h3 {
  font-size: 24px;
  margin-bottom: 15px;
  color: #303133;
}

.feature-card p {
  color: #606266;
  line-height: 1.6;
}

/* 使用流程 */
.process-section {
  padding: 80px 40px;
  background: #f5f7fa;
}

.process-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 1000px;
  margin: 0 auto;
}

.process-step {
  text-align: center;
  flex: 1;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: #409eff;
  color: white;
  font-size: 36px;
  font-weight: bold;
  border-radius: 50%;
  margin-bottom: 20px;
}

.step-content h3 {
  font-size: 20px;
  margin-bottom: 10px;
  color: #303133;
}

.step-content p {
  color: #606266;
}

.process-arrow {
  flex: 0 0 60px;
  color: #409eff;
}

/* 价格方案 */
.pricing-section {
  padding: 80px 40px;
  background: white;
}

.pricing-cards {
  display: flex;
  gap: 30px;
  justify-content: center;
  max-width: 1000px;
  margin: 0 auto;
}

.pricing-card {
  flex: 1;
  padding: 40px 30px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  text-align: center;
  position: relative;
  background: white;
  transition: transform 0.3s, box-shadow 0.3s;
}

.pricing-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.pricing-card.featured {
  border-color: #409eff;
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.2);
}

.featured-badge {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  background: #409eff;
  color: white;
  padding: 5px 20px;
  border-radius: 20px;
  font-size: 14px;
}

.pricing-card h3 {
  font-size: 24px;
  margin-bottom: 20px;
  color: #303133;
}

.pricing-card .price {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 30px;
}

.pricing-card ul {
  list-style: none;
  padding: 0;
  margin-bottom: 30px;
}

.pricing-card li {
  padding: 10px 0;
  color: #606266;
}

.pricing-card li::before {
  content: "✓";
  color: #67c23a;
  margin-right: 8px;
}

/* CTA区域 */
.cta-section {
  padding: 100px 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  text-align: center;
  color: white;
}

.cta-content h2 {
  font-size: 36px;
  margin-bottom: 20px;
}

.cta-content p {
  font-size: 20px;
  margin-bottom: 40px;
  opacity: 0.9;
}

.cta-content .el-button {
  min-width: 200px;
  height: 60px;
  font-size: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
  }
  
  .hero-title {
    font-size: 36px;
  }
  
  .hero-actions {
    justify-content: center;
  }
  
  .process-steps {
    flex-direction: column;
  }
  
  .process-arrow {
    transform: rotate(90deg);
    margin: 20px 0;
  }
  
  .pricing-cards {
    flex-direction: column;
  }
  
  .pricing-card.featured {
    transform: scale(1);
  }
}
</style>