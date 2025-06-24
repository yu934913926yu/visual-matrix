<template>
  <div class="recharge-container">
    <div class="recharge-header">
      <h2>充值中心</h2>
      <div class="balance-info">
        <span>当前积分余额：</span>
        <span class="balance-number">{{ userInfo?.points || 0 }}</span>
        <span>积分</span>
      </div>
    </div>

    <!-- 充值套餐 -->
    <div class="section">
      <h3>
        <el-icon><wallet /></el-icon>
        积分充值
      </h3>
      <div class="packages-grid" v-loading="loadingPackages">
        <div
          v-for="pkg in rechargePackages"
          :key="pkg.id"
          class="package-card"
          :class="{ 'popular': pkg.name.includes('标准') }"
          @click="selectPackage(pkg)"
        >
          <div v-if="pkg.name.includes('标准')" class="popular-tag">最受欢迎</div>
          <div class="package-header">
            <h4>{{ pkg.name }}</h4>
            <div class="price">
              <span class="currency">¥</span>
              <span class="amount">{{ pkg.cny_price }}</span>
            </div>
          </div>
          <div class="package-body">
            <div class="points-info">
              <el-icon><coin /></el-icon>
              <span class="points-number">{{ pkg.points_awarded }}</span>
              <span>积分</span>
            </div>
            <div v-if="pkg.bonus_points >
<div v-if="pkg.bonus_points > 0" class="bonus-tag">
              <el-icon><present /></el-icon>
              赠送 {{ pkg.bonus_points }} 积分
            </div>
            <p class="description">{{ pkg.description }}</p>
          </div>
          <el-button type="primary" size="large" round>立即充值</el-button>
        </div>
      </div>
    </div>

    <!-- 会员订阅 -->
    <div class="section">
      <h3>
        <el-icon><trophy /></el-icon>
        会员特权
      </h3>
      <div class="membership-grid" v-loading="loadingMemberships">
        <div
          v-for="tier in membershipTiers"
          :key="tier.id"
          class="membership-card"
          :class="{ 'premium': tier.name.includes('SVIP') }"
        >
          <div class="membership-header">
            <h4>{{ tier.name }}</h4>
            <el-tag :type="tier.name.includes('SVIP') ? 'danger' : 'warning'">
              {{ tier.generation_discount_percent }}% OFF
            </el-tag>
          </div>
          <div class="membership-features">
            <div class="feature">
              <el-icon><check /></el-icon>
              <span>图片生成享 {{ tier.generation_discount_percent }}% 折扣</span>
            </div>
            <div class="feature">
              <el-icon><check /></el-icon>
              <span>开通立送 {{ tier.points_grant }} 积分</span>
            </div>
            <div class="feature">
              <el-icon><check /></el-icon>
              <span>专属客服支持</span>
            </div>
            <div class="feature">
              <el-icon><check /></el-icon>
              <span>优先体验新功能</span>
            </div>
          </div>
          <div class="membership-pricing">
            <el-radio-group v-model="selectedBilling[tier.id]" @change="updatePrice(tier.id)">
              <el-radio-button label="monthly">
                <div class="billing-option">
                  <span>月付</span>
                  <span class="price">¥{{ tier.price_monthly }}/月</span>
                </div>
              </el-radio-button>
              <el-radio-button label="annually">
                <div class="billing-option">
                  <span>年付</span>
                  <span class="price">¥{{ tier.price_annually }}/年</span>
                  <el-tag type="success" size="small">省¥{{ tier.annual_savings }}</el-tag>
                </div>
              </el-radio-button>
            </el-radio-group>
          </div>
          <el-button 
            :type="tier.name.includes('SVIP') ? 'danger' : 'warning'" 
            size="large" 
            round
            @click="subscribeMembership(tier)"
          >
            立即开通
          </el-button>
        </div>
      </div>
    </div>

    <!-- 支付方式选择对话框 -->
    <el-dialog 
      v-model="showPaymentDialog" 
      title="选择支付方式" 
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="payment-info">
        <h4>{{ currentProduct?.name }}</h4>
        <div class="payment-amount">
          <span>支付金额：</span>
          <span class="amount">¥{{ currentProduct?.amount }}</span>
        </div>
      </div>
      
      <div class="payment-methods">
        <div 
          class="payment-method"
          :class="{ active: selectedPaymentMethod === 'alipay' }"
          @click="selectedPaymentMethod = 'alipay'"
        >
          <img src="/static/images/alipay.png" alt="支付宝">
          <span>支付宝</span>
          <el-icon v-if="selectedPaymentMethod === 'alipay'" class="check-icon">
            <circle-check />
          </el-icon>
        </div>
        <div 
          class="payment-method"
          :class="{ active: selectedPaymentMethod === 'wechat' }"
          @click="selectedPaymentMethod = 'wechat'"
        >
          <img src="/static/images/wechat-pay.png" alt="微信支付">
          <span>微信支付</span>
          <el-icon v-if="selectedPaymentMethod === 'wechat'" class="check-icon">
            <circle-check />
          </el-icon>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPaymentDialog = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="proceedPayment"
            :loading="processing"
          >
            确认支付
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 支付二维码对话框 -->
    <el-dialog 
      v-model="showQRDialog" 
      title="扫码支付" 
      width="400px"
      :close-on-click-modal="false"
      @close="cancelPayment"
    >
      <div class="qr-container">
        <div class="qr-code" v-if="paymentQRCode">
          <img :src="paymentQRCode" alt="支付二维码">
        </div>
        <div class="qr-info">
          <p>请使用{{ selectedPaymentMethod === 'alipay' ? '支付宝' : '微信' }}扫码支付</p>
          <p class="amount">¥{{ currentProduct?.amount }}</p>
        </div>
        <div class="qr-status">
          <el-icon class="loading"><loading /></el-icon>
          <span>等待支付...</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Wallet, 
  Coin, 
  Present, 
  Trophy, 
  Check, 
  CircleCheck,
  Loading 
} from '@element-plus/icons-vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export default {
  name: 'Recharge',
  components: {
    Wallet,
    Coin,
    Present,
    Trophy,
    Check,
    CircleCheck,
    Loading
  },
  setup() {
    const router = useRouter()
    const userInfo = ref(null)
    const rechargePackages = ref([])
    const membershipTiers = ref([])
    const loadingPackages = ref(false)
    const loadingMemberships = ref(false)
    const showPaymentDialog = ref(false)
    const showQRDialog = ref(false)
    const selectedPaymentMethod = ref('alipay')
    const currentProduct = ref(null)
    const processing = ref(false)
    const paymentQRCode = ref('')
    const selectedBilling = reactive({})
    const orderCheckInterval = ref(null)
    
    // 加载用户信息
    const loadUserInfo = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/auth/profile', {
          headers: { Authorization: `Bearer ${token}` }
        })
        userInfo.value = response.data.user
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    }
    
    // 加载充值套餐
    const loadRechargePackages = async () => {
      try {
        loadingPackages.value = true
        const response = await axios.get('/payment/recharge-packages')
        rechargePackages.value = response.data.packages
      } catch (error) {
        ElMessage.error('获取充值套餐失败')
      } finally {
        loadingPackages.value = false
      }
    }
    
    // 加载会员等级
    const loadMembershipTiers = async () => {
      try {
        loadingMemberships.value = true
        const response = await axios.get('/payment/membership-tiers')
        membershipTiers.value = response.data.tiers
        
        // 初始化选择的计费周期
        response.data.tiers.forEach(tier => {
          selectedBilling[tier.id] = 'monthly'
        })
      } catch (error) {
        ElMessage.error('获取会员等级失败')
      } finally {
        loadingMemberships.value = false
      }
    }
    
    // 选择充值套餐
    const selectPackage = (pkg) => {
      currentProduct.value = {
        type: 'points',
        id: pkg.id,
        name: pkg.name,
        amount: pkg.cny_price
      }
      showPaymentDialog.value = true
    }
    
    // 订阅会员
    const subscribeMembership = (tier) => {
      const billing = selectedBilling[tier.id] || 'monthly'
      currentProduct.value = {
        type: 'membership',
        id: tier.id,
        name: `${tier.name} - ${billing === 'monthly' ? '月付' : '年付'}`,
        amount: billing === 'monthly' ? tier.price_monthly : tier.price_annually,
        billing_cycle: billing
      }
      showPaymentDialog.value = true
    }
    
    // 更新价格显示
    const updatePrice = (tierId) => {
      // 价格会自动根据选择更新
    }
    
    // 确认支付
    const proceedPayment = async () => {
      if (!selectedPaymentMethod.value) {
        ElMessage.warning('请选择支付方式')
        return
      }
      
      processing.value = true
      
      try {
        const token = localStorage.getItem('token')
        const response = await axios.post('/payment/create-order', {
          product_type: currentProduct.value.type,
          product_id: currentProduct.value.id,
          payment_method: selectedPaymentMethod.value,
          billing_cycle: currentProduct.value.billing_cycle
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        if (response.data.qr_code || response.data.payment_url) {
          paymentQRCode.value = response.data.qr_code || response.data.payment_url
          showPaymentDialog.value = false
          showQRDialog.value = true
          
          // 开始轮询检查订单状态
          startOrderCheck(response.data.order_id)
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.error || '创建订单失败')
      } finally {
        processing.value = false
      }
    }
    
    // 轮询检查订单状态
    const startOrderCheck = (orderId) => {
      orderCheckInterval.value = setInterval(async () => {
        try {
          const token = localStorage.getItem('token')
          const response = await axios.get(`/payment/order-status/${orderId}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          
          if (response.data.status === 'paid') {
            clearInterval(orderCheckInterval.value)
            showQRDialog.value = false
            ElMessage.success('支付成功！')
            
            // 刷新用户信息
            await loadUserInfo()
            
            // 如果是会员订阅，跳转到会员中心
            if (currentProduct.value.type === 'membership') {
              router.push('/member-center')
            }
          }
        } catch (error) {
          console.error('检查订单状态失败:', error)
        }
      }, 2000) // 每2秒检查一次
    }
    
    // 取消支付
    const cancelPayment = () => {
      if (orderCheckInterval.value) {
        clearInterval(orderCheckInterval.value)
      }
      paymentQRCode.value = ''
    }
    
    onMounted(() => {
      loadUserInfo()
      loadRechargePackages()
      loadMembershipTiers()
    })
    
    onUnmounted(() => {
      if (orderCheckInterval.value) {
        clearInterval(orderCheckInterval.value)
      }
    })
    
    return {
      userInfo,
      rechargePackages,
      membershipTiers,
      loadingPackages,
      loadingMemberships,
      showPaymentDialog,
      showQRDialog,
      selectedPaymentMethod,
      currentProduct,
      processing,
      paymentQRCode,
      selectedBilling,
      selectPackage,
      subscribeMembership,
      updatePrice,
      proceedPayment,
      cancelPayment
    }
  }
}
</script>

<style scoped>
.recharge-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.recharge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.recharge-header h2 {
  margin: 0;
  font-size: 28px;
}

.balance-info {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 16px;
}

.balance-number {
  font-size: 36px;
  font-weight: bold;
}

.section {
  margin-bottom: 50px;
}

.section h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 30px;
  font-size: 24px;
  color: #303133;
}

/* 充值套餐网格 */
.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.package-card {
  position: relative;
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.package-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.package-card.popular {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.popular-tag {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: #409eff;
  color: white;
  padding: 4px 16px;
  border-radius: 12px;
  font-size: 12px;
}

.package-header h4 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #303133;
}

.price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-bottom: 20px;
}

.currency {
  font-size: 18px;
  color: #f56c6c;
}

.amount {
  font-size: 36px;
  font-weight: bold;
  color: #f56c6c;
}

.points-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 15px;
  font-size: 18px;
  color: #409eff;
}

.points-number {
  font-size: 28px;
  font-weight: bold;
}

.bonus-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f0f9ff;
  color: #409eff;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
  margin-bottom: 15px;
}

.description {
  color: #909399;
  margin-bottom: 20px;
}

/* 会员卡片 */
.membership-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
}

.membership-card {
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 40px;
  transition: all 0.3s;
}

.membership-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.membership-card.premium {
  border-color: #f56c6c;
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
}

.membership-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.membership-header h4 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.membership-features {
  margin-bottom: 30px;
}

.feature {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  color: #606266;
}

.feature .el-icon {
  color: #67c23a;
}

.membership-pricing {
  margin-bottom: 30px;
}

.billing-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px;
}

.billing-option .price {
  font-weight: bold;
  color: #303133;
}

/* 支付对话框 */
.payment-info {
  text-align: center;
  margin-bottom: 30px;
}

.payment-info h4 {
  margin-bottom: 15px;
}

.payment-amount {
  font-size: 18px;
}

.payment-amount .amount {
  font-size: 28px;
  font-weight: bold;
  color: #f56c6c;
}

.payment-methods {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 20px;
}

.payment-method {
  position: relative;
  padding: 20px 30px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.payment-method:hover {
  border-color: #409eff;
}

.payment-method.active {
  border-color: #409eff;
  background: #f0f9ff;
}

.payment-method img {
  width: 80px;
  height: 80px;
  object-fit: contain;
  margin-bottom: 10px;
}

.check-icon {
  position: absolute;
  top: 10px;
  right: 10px;
  color: #409eff;
  font-size: 20px;
}

/* 二维码对话框 */
.qr-container {
  text-align: center;
}

.qr-code {
  margin-bottom: 20px;
}

.qr-code img {
  width: 200px;
  height: 200px;
}

.qr-info {
  margin-bottom: 20px;
}

.qr-info .amount {
  font-size: 24px;
  font-weight: bold;
  color: #f56c6c;
  margin-top: 10px;
}

.qr-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #909399;
}

.qr-status .loading {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style><template>
  <div class="recharge-container">
    <div class="recharge-header">
      <h2>充值中心</h2>
      <div class="balance-info">
        <span>当前积分余额：</span>
        <span class="balance-number">{{ userInfo?.points || 0 }}</span>
        <span>积分</span>
      </div>
    </div>

    <!-- 充值套餐 -->
    <div class="section">
      <h3>
        <el-icon><wallet /></el-icon>
        积分充值
      </h3>
      <div class="packages-grid" v-loading="loadingPackages">
        <div
          v-for="pkg in rechargePackages"
          :key="pkg.id"
          class="package-card"
          :class="{ 'popular': pkg.name.includes('标准') }"
          @click="selectPackage(pkg)"
        >
          <div v-if="pkg.name.includes('标准')" class="popular-tag">最受欢迎</div>
          <div class="package-header">
            <h4>{{ pkg.name }}</h4>
            <div class="price">
              <span class="currency">¥</span>
              <span class="amount">{{ pkg.cny_price }}</span>
            </div>
          </div>
          <div class="package-body">
            <div class="points-info">
              <el-icon><coin /></el-icon>
              <span class="points-number">{{ pkg.points_awarded }}</span>
              <span>积分</span>
            </div>
            <div v-if="pkg.bonus_points >