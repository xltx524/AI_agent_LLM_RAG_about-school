<template>
  <!-- [修改] 动态绑定 'dark-mode' 类 -->
  <div class="register-container" :class="{ 'dark-mode': isDarkMode }">
    <div class="register-box">
      <div class="register-header">
        <div class="logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 4L4 8V16L12 20L20 16V8L12 4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 12L20 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 12L4 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 12V20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="register-title">新用户注册</h1>
        <p class="register-subtitle">加入协和学院招生咨询系统</p>
      </div>
      <el-form
          :model="registerForm"
          :rules="rules"
          ref="registerFormRef"
          class="register-form"
          label-position="top"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="name">
              <el-input v-model="registerForm.name" placeholder="请输入您的姓名" clearable size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="账号" prop="account">
              <el-input v-model="registerForm.account" placeholder="请输入您的账号" clearable size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password size="large">
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password size="large" @keyup.enter="register">
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="性别" prop="sex">
              <el-radio-group v-model="registerForm.sex" size="large">
                <el-radio-button label="男" />
                <el-radio-button label="女" />
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年龄" prop="age">
              <el-input-number v-model="registerForm.age" :min="1" :max="100" placeholder="请输入年龄" size="large" controls-position="right" style="width: 100%;"/>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="电话" prop="phoneNum">
          <el-input v-model="registerForm.phoneNum" placeholder="请输入电话号码" clearable size="large">
            <template #prefix><el-icon><Phone /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="register" :disabled="register_disabled" class="register-button" size="large">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        <p>已有账号? <el-link type="primary" :underline="false" @click="goToLogin">立即登录</el-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, getCurrentInstance } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import axios from 'axios';
import { User, Lock, Phone } from '@element-plus/icons-vue';

const app = getCurrentInstance();
const httpUrl = app.appContext.config.globalProperties.$httpUrl;

const router = useRouter();
const register_disabled = ref(false);
const registerFormRef = ref(null);
const isDarkMode = ref(false); // [新增] 暗黑模式状态

const registerForm = reactive({
  name: '',
  account: '',
  password: '',
  confirmPassword: '',
  sex: '', // 页面上绑定的是字符串 "男" 或 "女"
  age: null,
  phoneNum: '',
  roleId: 2,
  isValid: 'Y',
});

// [新增] 组件挂载时初始化主题
onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    isDarkMode.value = savedTheme === 'dark';
  } else {
    isDarkMode.value = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
});

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'));
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致!'));
  } else {
    callback();
  }
};

const validateAccountUnique = async (rule, value, callback) => {
  if (!value) return callback(new Error('请输入账号'));
  if (value.length < 3 || value.length > 15) return callback();
  try {
    const response = await axios.get(`${httpUrl}/user/findByNo?account=${value}`);
    // 后端返回 Result.fail("账号已存在")，其code可能不是200，或者code是200但msg是"账号已存在"
    // 假设后端成功时返回 code: 200, msg: "账号可用"
    // 失败时返回 code: 500 (或其他), msg: "账号已存在"
    // 或者 code: 200, msg: "账号已存在" (如果将失败也包装成200)
    // 最佳实践是后端在失败时返回非200状态码或明确的失败code
    // 这里我们根据后端 `findByNo` 方法返回的 `Result.fail("账号已存在")` 来判断
    if (response.data.code !== 200 && response.data.msg === '账号已存在') { // 根据你的后端Result类判断
      callback(new Error('该账号已存在，请更换'));
    } else if (response.data.code === 200 && response.data.msg === '账号已存在') { // 兼容后端将失败也返回200的情况
      callback(new Error('该账号已存在，请更换'));
    } else {
      callback();
    }
  } catch (error) {
    console.error("检查账号唯一性失败:", error);
    callback(new Error('网络错误，无法检查账号唯一性'));
  }
};

const validateNameUnique = async (rule, value, callback) => {
  if (!value) return callback(new Error('请输入用户名'));
  if (value.length < 2 || value.length > 20) return callback();
  try {
    const response = await axios.get(`${httpUrl}/user/findByName?name=${value}`);
    // 同理，根据后端 `findByName` 方法返回的 `Result.fail("用户名已存在")` 来判断
    if (response.data.code !== 200 && response.data.msg === '用户名已存在') { // 根据你的后端Result类判断
      callback(new Error('该用户名已存在，请更换'));
    } else if (response.data.code === 200 && response.data.msg === '用户名已存在') { // 兼容后端将失败也返回200的情况
      callback(new Error('该用户名已存在，请更换'));
    } else {
      callback();
    }
  } catch (error) {
    console.error("检查用户名唯一性失败:", error);
    callback(new Error('网络错误，无法检查用户名唯一性'));
  }
};

const rules = reactive({
  name: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { validator: validateNameUnique, trigger: 'blur' }
  ],
  account: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 15, message: '账号长度在 3 到 15 个字符', trigger: 'blur' },
    { validator: validateAccountUnique, trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validatePass2, trigger: 'blur' }
  ],
  sex: [
    { required: true, message: '请选择性别', trigger: 'change' }
  ],
  age: [
    { required: true, message: '请输入年龄', trigger: 'blur' },
    { type: 'number', message: '年龄必须是数字', trigger: 'blur' },
  ],
  phoneNum: [
    { required: true, message: '请输入电话号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码', trigger: 'blur' }
  ],
});

const register = () => {
  registerFormRef.value.validate((valid) => {
    if (valid) {
      register_disabled.value = true;
      // 复制表单数据，并排除 confirmPassword
      const { confirmPassword, ...dataToSend } = registerForm;

      // --- 关键修改：将 sex 字段从字符串转换为数字 ---
      let sexValueToSend;
      if (dataToSend.sex === '男') {
        sexValueToSend = 0; // 假设 0 代表男性
      } else if (dataToSend.sex === '女') {
        sexValueToSend = 1; // 假设 1 代表女性
      } else {
        sexValueToSend = null; // 如果没有选择或者有其他值，可以设置为 null 或一个默认值
      }
      dataToSend.sex = sexValueToSend; // 更新要发送的数据中的 sex 字段
      // --- 结束关键修改 ---

      axios.post(`${httpUrl}/user/save`, dataToSend)
          .then(res => res.data)
          .then(res => {
            if (res.code === 200) {
              ElMessage.success('注册成功！请前往登录页进行登录。');
              router.push('/login');
            } else {
              register_disabled.value = false;
              ElMessage.error(res.msg || '注册失败，请稍后再试！');
            }
          })
          .catch(error => {
            register_disabled.value = false;
            if (error.response) {
              // 尝试从错误响应中获取更详细的错误信息
              ElMessage.error(`注册失败：${error.response.status} - ${error.response.data.msg || '服务器错误'}`);
            } else {
              ElMessage.error('注册请求发生未知错误，请检查网络或后端服务！');
            }
          });
    } else {
      ElMessage.warning('请检查输入项！');
    }
  });
};

const goToLogin = () => {
  router.push('/login');
};
</script>

<style scoped>
/* --- 基础样式 --- */
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-image: url('https://source.unsplash.com/random/1600x900/?university,campus');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  transition: background-image 0.5s ease-in-out;
}

.register-box {
  width: 100%;
  max-width: 600px;
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

.logo svg { width: 40px; height: 40px; }

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-title {
  font-size: 26px;
  font-weight: 600;
  color: #1a237e;
  margin-bottom: 8px;
  letter-spacing: 1px;
  transition: color 0.3s;
}

.register-subtitle {
  color: #5f6368;
  font-size: 15px;
  margin: 0;
  font-weight: 400;
  transition: color 0.3s;
}

.register-form { margin-top: 30px; }
.el-form-item { margin-bottom: 22px; }

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #3f51b5;
  padding-bottom: 8px !important;
  font-size: 14px;
  transition: color 0.3s;
}

.el-input, .el-input-number, .el-radio-group {
  --el-input-border-radius: 8px;
  --el-input-height: 48px;
  --el-input-bg-color: rgba(244, 246, 248, 0.8);
  --el-input-text-color: #333;
  --el-input-border-color: #e0e0e0;
  --el-input-hover-border-color: #3f51b5;
  --el-input-placeholder-color: #999;
}

:deep(.el-input__wrapper), :deep(.el-input-number) {
  transition: all 0.3s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-input__wrapper.is-focus), :deep(.el-input-number.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-input-hover-border-color) inset !important;
}

:deep(.el-input__prefix) {
  padding-right: 10px;
  color: #5f6368;
  transition: color 0.3s;
}

.register-button {
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

.register-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(26, 86, 219, 0.3);
}

.register-button:active { transform: translateY(0); }

.register-footer {
  margin-top: 30px;
  text-align: center;
  color: #5f6368;
  font-size: 14px;
  transition: color 0.3s;
}

.register-footer p { margin-bottom: 0; }

/* ----------------------------- */
/* --- [新增] 暗黑模式样式 --- */
/* ----------------------------- */
.register-container.dark-mode {
  background-image: url('https://source.unsplash.com/random/1600x900/?night,city,stars');
}

.register-container.dark-mode .register-box {
  background: rgba(28, 35, 48, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.register-container.dark-mode .logo {
  color: #63b3ed;
  background: rgba(99, 179, 237, 0.1);
  border-color: #63b3ed;
}

.register-container.dark-mode .register-title {
  color: #edf2f7;
}

.register-container.dark-mode .register-subtitle {
  color: #a0aec0;
}

.register-container.dark-mode :deep(.el-form-item__label) {
  color: #63b3ed;
}

.register-container.dark-mode .el-input,
.register-container.dark-mode .el-input-number {
  --el-input-bg-color: #2d3748;
  --el-input-text-color: #e2e8f0;
  --el-input-border-color: #4a5568;
  --el-input-hover-border-color: #63b3ed;
  --el-input-placeholder-color: #718096;
}

.register-container.dark-mode :deep(.el-input__prefix) {
  color: #a0aec0;
}

.register-container.dark-mode :deep(.el-radio-button__inner) {
  background-color: #2d3748;
  color: #e2e8f0;
  border-color: #4a5568;
  box-shadow: none !important;
}

.register-container.dark-mode :deep(.el-radio-button__original-radio:checked+.el-radio-button__inner) {
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: white;
}

.register-container.dark-mode :deep(.el-link--inner) {
  color: #63b3ed;
}

.register-container.dark-mode .register-footer {
  color: #a0aec0;
}
</style>