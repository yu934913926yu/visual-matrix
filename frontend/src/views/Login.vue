<template>
  <div class="login-container">
    <div class="login-box">
      <h2>登录 视觉矩阵</h2>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="register-link">
        <span>还没有账号？</span>
        <el-button type="text" @click="showRegister = true">立即注册</el-button>
      </div>
    </div>

    <!-- 注册对话框 -->
    <el-dialog v-model="showRegister" title="注册新账号" width="400px">
      <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRegister = false">取消</el-button>
          <el-button type="primary" @click="handleRegister" :loading="registerLoading">
            注册
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const loginFormRef = ref()
    const registerFormRef = ref()
    
    const loginForm = ref({
      username: '',
      password: ''
    })
    
    const registerForm = ref({
      username: '',
      password: '',
      confirmPassword: ''
    })
    
    const loading = ref(false)
    const registerLoading = ref(false)
    const showRegister = ref(false)
    
    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }
    
    const registerRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '用户名长度在3到20个字符', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请确认密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== registerForm.value.password) {
              callback(new Error('两次输入的密码不一致'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }
    
    const handleLogin = async () => {
      try {
        await loginFormRef.value.validate()
        loading.value = true
        
        const response = await axios.post('/auth/login', loginForm.value)
        
        if (response.data.token) {
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('userInfo', JSON.stringify(response.data.user))
          
          ElMessage.success('登录成功')
          router.push('/dashboard')
        }
      } catch (error) {
        console.error('登录失败:', error)
        ElMessage.error(error.response?.data?.error || '登录失败')
      } finally {
        loading.value = false
      }
    }
    
    const handleRegister = async () => {
      try {
        await registerFormRef.value.validate()
        registerLoading.value = true
        
        const response = await axios.post('/auth/register', {
          username: registerForm.value.username,
          password: registerForm.value.password
        })
        
        ElMessage.success('注册成功！请登录')
        showRegister.value = false
        loginForm.value.username = registerForm.value.username
        registerForm.value = { username: '', password: '', confirmPassword: '' }
      } catch (error) {
        console.error('注册失败:', error)
        ElMessage.error(error.response?.data?.error || '注册失败')
      } finally {
        registerLoading.value = false
      }
    }
    
    return {
      loginForm,
      registerForm,
      loginFormRef,
      registerFormRef,
      loading,
      registerLoading,
      showRegister,
      rules,
      registerRules,
      handleLogin,
      handleRegister
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  width: 400px;
}

.login-box h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.register-link {
  text-align: center;
  margin-top: 20px;
}
</style>