<template>
  <!-- [修改] 动态绑定 'dark-mode' 类 -->
  <div class="login-container" :class="{ 'dark-mode': isDarkMode }">
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 4L4 8V16L12 20L20 16V8L12 4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 12L20 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 12L4 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 12V20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="login-title">协和学院招生咨询系统</h1>
        <p class="login-subtitle">开启您的学术之旅</p>
      </div>
      <el-form
          :model="loginForm"
          :rules="rules"
          ref="loginFormRef"
          class="login-form"
          label-position="top"
      >
        <el-form-item label="账号" prop="account">
          <el-input
              v-model="loginForm.account"
              placeholder="请输入您的账号"
              clearable
              size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入您的密码"
              show-password
              size="large"
              @keyup.enter="confirm"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <div class="form-actions">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <el-link type="primary" :underline="false">忘记密码?</el-link>
        </div>
        <el-form-item>
          <el-button
              type="primary"
              @click="confirm"
              :disabled="confirm_disabled"
              class="login-button"
              size="large"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <p>还没有账号? <el-link type="primary" :underline="false" @click="goToRegister">立即注册</el-link></p>
        <div class="social-login">
          <el-tooltip content="使用微信登录" placement="top">
            <el-button circle class="social-icon wechat">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8.5 14c1.4 0 2.5-1.1 2.5-2.5S9.9 9 8.5 9 6 10.1 6 11.5 7.1 14 8.5 14zm7 0c1.4 0 2.5-1.1 2.5-2.5S16.9 9 15.5 9 13 10.1 13 11.5 14.1 14 15.5 14z"/><path d="M12 2C6.5 2 2 5.6 2 10c0 2.2 1.2 4.2 3.1 5.5-.2.7-.7 2.5-.8 3.1-.1.6.4.6.7.3.3-.3 1.9-1.8 2.6-2.5.8.2 1.6.3 2.4.3 5.5 0 10-3.6 10-8S17.5 2 12 2zm0 14c-.8 0-1.6-.1-2.4-.3l-.6-.1-.4.4c-.5.5-1.6 1.5-2.3 2.1.1-.6.4-1.9.5-2.3l.1-.6-.5-.3C4.2 13.4 3 11.7 3 10c0-3.5 4-6 9-6s9 2.5 9 6-4 6-9 6z"/></svg>
            </el-button>
          </el-tooltip>
          <el-tooltip content="使用QQ登录" placement="top">
            <el-button circle class="social-icon qq">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8z"/><path d="M12 6c-3.3 0-6 2.7-6 6s2.7 6 6 6 6-2.7 6-6-2.7-6-6-6zm0 10c-2.2 0-4-1.8-4-4s1.8-4 4-4 4 1.8 4 4-1.8 4-4 4z"/><path d="M12 10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, getCurrentInstance, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import axios from 'axios'; // 确保 axios 已导入
import { User, Lock } from '@element-plus/icons-vue';

const app = getCurrentInstance();
const httpUrl = app.appContext.config.globalProperties.$httpUrl;

const router = useRouter();
const confirm_disabled = ref(false);
const loginFormRef = ref(null);
const rememberMe = ref(false);
const isDarkMode = ref(false); // [新增] 暗黑模式状态

const loginForm = reactive({
  account: '',
  password: '',
});

const rules = reactive({
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }, { min: 3, max: 15, message: '账号长度在 3 到 15 个字符', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }],
});

// [新增] 应用暗黑模式的辅助函数
const applyDarkMode = (isDark) => {
  if (isDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
};

onMounted(() => {
  // 检查是否已登录，如果已登录则直接跳转
  // 此时 isAuthenticated 的判断应该同时检查 token 和 CurUser
  const token = localStorage.getItem('token');
  const storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');

  if (token && storedUser) {
    router.replace('/');
    return; // 提前返回，无需执行后面的主题逻辑
  }

  // --- [新增] 主题初始化逻辑 ---
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    // 优先使用本地存储的设置
    isDarkMode.value = savedTheme === 'dark';
  } else {
    // 否则，检测系统主题设置
    isDarkMode.value = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  // 将主题状态应用到 <html> 和组件本身
  applyDarkMode(isDarkMode.value);
});


const confirm = () => {
  loginFormRef.value.validate((valid) => {
    if (valid) {
      confirm_disabled.value = true;
      axios.post(`${httpUrl}/user/login`, loginForm)
          .then(res => res.data)
          .then(res => {
            if (res.code === 200) {
              if (!res.data.user || !res.data.user.role || !res.data.token) { // 检查 token 是否存在
                ElMessage.error('登录成功，但无法获取完整的用户或认证信息，请联系管理员！');
                confirm_disabled.value = false;
                return;
              }

              const token = res.data.token; // 获取后端返回的 JWT Token
              const user = res.data.user;   // 获取后端返回的用户信息

              // [修改] 登录成功后，保存主题设置，以便进入主界面后保持一致
              localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light');
              localStorage.setItem('token', token); // <-- 【新增】存储 JWT Token

              if (rememberMe.value) {
                localStorage.setItem("CurUser", JSON.stringify(user)); // 使用获取到的 user 对象
                localStorage.setItem("id",user.id)
              } else {
                sessionStorage.setItem("CurUser", JSON.stringify(user)); // 使用获取到的 user 对象
              }

              ElMessage.success('登录成功！');
              router.replace('/');

            } else {
              confirm_disabled.value = false;
              ElMessage.error(res.msg || '用户名或密码错误！');
            }
          })
          .catch(error => {
            confirm_disabled.value = false;
            // 改进错误处理，显示更具体的网络错误信息
            if (error.response) {
              ElMessage.error(`登录失败：${error.response.status} - ${error.response.data.msg || '服务器错误'}`);
            } else if (error.request) {
              ElMessage.error('登录请求无响应，请检查网络或后端服务是否运行！');
            } else {
              ElMessage.error('登录请求发生未知错误！' + error.message);
            }
            console.error('登录请求失败详情:', error); // 打印完整错误信息用于调试
          });
    } else {
      ElMessage.warning('请检查输入项！');
    }
  });
};

const goToRegister = () => {
  router.push('/register');
};
</script>

<style scoped>
/* --- 基础样式 --- */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
  padding: 20px;
  background-image: url('https://source.unsplash.com/random/1600x900/?university,campus');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  transition: background-image 0.5s ease-in-out;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 40px;
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  animation: fadeInUp 0.6s ease-out;
  transition: background 0.3s, border 0.3s;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.logo {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1a56db;
  background: rgba(26, 86, 219, 0.1);
  border-radius: 50%;
  border: 2px solid #1a56db;
  transition: color 0.3s, background 0.3s, border-color 0.3s;
}

.logo svg {
  width: 40px;
  height: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-title {
  font-size: 26px;
  font-weight: 600;
  color: #1a237e;
  margin-bottom: 8px;
  letter-spacing: 1px;
  transition: color 0.3s;
}

.login-subtitle {
  color: #5f6368;
  font-size: 15px;
  margin: 0;
  font-weight: 400;
  transition: color 0.3s;
}

.login-form {
  margin-top: 30px;
}

.el-form-item {
  margin-bottom: 22px;
}

/* 使用 :deep() 来修改 Element Plus 内部组件的 label 样式 */
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #3f51b5;
  padding-bottom: 8px !important;
  font-size: 14px;
  transition: color 0.3s;
}

.el-input {
  --el-input-border-radius: 8px;
  --el-input-height: 48px;
  --el-input-bg-color: rgba(244, 246, 248, 0.8);
  --el-input-text-color: #333;
  --el-input-border-color: #e0e0e0;
  --el-input-hover-border-color: #3f51b5;
  --el-input-placeholder-color: #999;
}

:deep(.el-input__wrapper) {
  transition: all 0.3s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-input-hover-border-color) inset !important;
}

:deep(.el-input__prefix) {
  padding-right: 10px;
  color: #5f6368;
  transition: color 0.3s;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
  height: 48px;
  font-weight: 500;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(to right, #1a56db, #3f51b5);
  border: none;
  transition: all 0.3s ease;
  letter-spacing: 2px;
  margin-top: 10px;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(26, 86, 219, 0.3);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  color: #5f6368;
  font-size: 14px;
  transition: color 0.3s;
}

.login-footer p {
  margin-bottom: 20px;
}

.social-login {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.social-icon {
  width: 40px;
  height: 40px;
  transition: all 0.3s ease;
  border: none;
}

.social-icon.wechat { background: #07c160; color: white; }
.social-icon.qq { background: #12b7f5; color: white; }

.social-icon:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.social-icon svg { width: 20px; height: 20px; }

/* ----------------------------- */
/* --- [新增] 暗黑模式样式 --- */
/* ----------------------------- */

/* 当组件根元素有 .dark-mode 类时，应用以下样式 */
.login-container.dark-mode {
  background-image: url('https://source.unsplash.com/random/1600x900/?night,city,stars');
  background-color: #1a202c;
}

.login-container.dark-mode .login-box {
  background: rgba(28, 35, 48, 0.85); /* 深色半透明背景 */
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.login-container.dark-mode .logo {
  color: #63b3ed; /* 浅蓝色 */
  background: rgba(99, 179, 237, 0.1);
  border-color: #63b3ed;
}

.login-container.dark-mode .login-title {
  color: #edf2f7; /* 浅灰色文字 */
}

.login-container.dark-mode .login-subtitle {
  color: #a0aec0; /* 较暗的灰色文字 */
}

.login-container.dark-mode :deep(.el-form-item__label) {
  color: #63b3ed; /* 浅蓝色标签 */
}

/* 通过修改CSS变量来改变输入框样式 */
.login-container.dark-mode .el-input {
  --el-input-bg-color: #2d3748;
  --el-input-text-color: #e2e8f0;
  --el-input-border-color: #4a5568;
  --el-input-hover-border-color: #63b3ed;
  --el-input-placeholder-color: #718096;
}

.login-container.dark-mode :deep(.el-input__prefix) {
  color: #a0aec0;
}

/* 修改复选框和链接的颜色 */
.login-container.dark-mode :deep(.el-checkbox__label) {
  color: #a0aec0;
}
.login-container.dark-mode :deep(.el-link--inner) {
  color: #63b3ed;
}

.login-container.dark-mode .login-footer {
  color: #a0aec0;
}
</style>