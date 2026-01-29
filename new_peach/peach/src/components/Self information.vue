<template>
  <div class="home-container">
    <div class="welcome-card">
      <!-- 1. 圆形头像占位符 - 美化版 -->
      <div class="avatar-container">
        <div class="avatar-placeholder">
          <img :src="randomAvatarUrl" alt="User Avatar" class="avatar-img">
          <div class="avatar-border"></div>
          <div class="avatar-shadow"></div>
        </div>
      </div>

      <h1 class="welcome-title">{{ '欢迎你！' + user.name }}</h1>
      <el-divider class="custom-divider" />

      <!-- 2. 信息内容分组：基本信息 -->
      <div class="info-group">
        <h2 class="group-title">基本信息</h2>
        <el-descriptions
            class="user-info-basic"
            :column="2"
            size="large"
            border
        >
          <el-descriptions-item>
            <template #label>
              <el-icon><user /></el-icon>
              账号
            </template>
            {{ user.account }}
          </el-descriptions-item>

          <el-descriptions-item>
            <template #label>
              <el-icon><location /></el-icon>
              性别
            </template>
            <el-tag
                :type="user.sex === '1' ? 'primary' : 'danger'"
                effect="light"
                class="gender-tag"
            >
              <el-icon :class="user.sex == 1 ? 'male-icon' : 'female-icon'">
                <component :is="user.sex == 1 ? 'male' : 'female'" />
              </el-icon>
              {{ user.sex == 1 ? "男" : "女" }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider class="custom-divider" />

      <!-- 2. 信息内容分组：联系方式 -->
      <div class="info-group">
        <h2 class="group-title">联系方式</h2>
        <el-descriptions
            class="user-info-contact"
            :column="2"
            size="large"
            border
        >
          <el-descriptions-item>
            <template #label>
              <el-icon><iphone /></el-icon>
              电话
            </template>
            {{ user.phoneNum }}
          </el-descriptions-item>

          <el-descriptions-item>
            <template #label>
              <el-icon><tickets /></el-icon>
              角色
            </template>
            <el-tag type="success" effect="light" class="role-tag">
              {{ user.roleId == 0 ? "超级管理员" : (user.roleId == 1 ? "管理员" : "用户") }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 6. 底部按钮 -->
      <div class="card-actions">
        <el-button type="primary" round class="action-button" @click="handleEditProfile">
          <el-icon><edit /></el-icon>
          编辑资料
        </el-button>
        <el-button type="info" round class="action-button" @click="handleChangePassword">
          <el-icon><lock /></el-icon>
          修改密码
        </el-button>
      </div>
    </div>

    <!-- 编辑资料 Dialog -->
    <el-dialog
        v-model="editProfileDialogVisible"
        title="编辑个人资料"
        width="600px"
        :show-close="false"
        class="custom-dialog"
        center
        :close-on-click-modal="false"
    >
      <div class="dialog-content">
        <el-form
            label-width="100px"
            label-position="left"
            :model="editProfileForm"
            :rules="editProfileRules"
            ref="editProfileFormRef"
        >
          <div class="form-grid">
            <el-form-item label="用户名" prop="name">
              <el-input v-model="editProfileForm.name" placeholder="请输入用户名" clearable>
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="账号" prop="account">
              <el-input v-model="editProfileForm.account" placeholder="账号不可修改" disabled>
                <template #prefix><el-icon><Key /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="性别" prop="sex">
              <el-radio-group v-model="editProfileForm.sex">
                <el-radio-button label="1">男</el-radio-button>
                <el-radio-button label="2">女</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="电话" prop="phoneNum">
              <el-input v-model="editProfileForm.phoneNum" placeholder="请输入电话号码" clearable>
                <template #prefix><el-icon><Phone /></el-icon></template>
              </el-input>
            </el-form-item>

            <!-- 角色信息作为展示，不可修改 -->
            <el-form-item label="角色" prop="roleId">
              <el-select v-model="editProfileForm.roleId" placeholder="角色不可修改" style="width: 100%" disabled>
                <el-option label="超级管理员" :value="0" />
                <el-option label="管理员" :value="1" />
                <el-option label="用户" :value="2" />
              </el-select>
            </el-form-item>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelEditProfile" size="large">取消</el-button>
          <el-button
              type="primary"
              @click="confirmEditProfile"
              size="large"
              :loading="editProfileLoading"
          >
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 修改密码 Dialog -->
    <el-dialog
        v-model="changePasswordDialogVisible"
        title="修改密码"
        width="500px"
        :show-close="false"
        class="custom-dialog"
        center
        :close-on-click-modal="false"
    >
      <div class="dialog-content">
        <el-form
            label-width="100px"
            label-position="left"
            :model="changePasswordForm"
            :rules="changePasswordRules"
            ref="changePasswordFormRef"
        >
          <el-form-item label="旧密码" prop="oldPassword">
            <el-input
                v-model="changePasswordForm.oldPassword"
                type="password"
                placeholder="请输入旧密码"
                show-password
            >
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>

          <el-form-item label="新密码" prop="newPassword">
            <el-input
                v-model="changePasswordForm.newPassword"
                type="password"
                placeholder="请输入新密码"
                show-password
            >
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>

          <el-form-item label="确认新密码" prop="confirmNewPassword">
            <el-input
                v-model="changePasswordForm.confirmNewPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
            >
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelChangePassword" size="large">取消</el-button>
          <el-button
              type="primary"
              @click="confirmChangePassword"
              size="large"
              :loading="changePasswordLoading"
          >
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { User, Iphone, Location, Tickets, Male, Female, Edit, Lock, Key, Phone } from '@element-plus/icons-vue'
import { ref, onMounted, reactive, getCurrentInstance } from 'vue'
import axios from 'axios';
import { ElMessage } from 'element-plus';

const { proxy } = getCurrentInstance();
const httpUrl = proxy.$httpUrl;

const user = ref({
  id: null,
  name: '加载中...',
  account: 'N/A',
  phoneNum: 'N/A',
  sex: '0',
  roleId: -1
});

const randomAvatarUrl = ref('');

// --- 编辑资料相关状态 ---
const editProfileDialogVisible = ref(false);
const editProfileFormRef = ref(null);
const editProfileLoading = ref(false);
const editProfileForm = reactive({
  id: null,
  name: '',
  phoneNum: '',
  sex: '',
  account: '',
  roleId: null
});

// 【新增】用户名唯一性校验规则（适用于编辑场景）
const validateNameUnique = async (rule, value, callback) => {
  if (!value) {
    return callback(new Error('请输入用户名'));
  }
  // 如果新用户名与当前用户的原始用户名相同，则通过校验
  if (value === user.value.name) {
    return callback();
  }
  // 长度校验
  if (value.length < 2 || value.length > 20) {
    return callback(); // 让其他规则处理长度
  }
  try {
    const response = await axios.get(`${httpUrl}/user/findByName?name=${value}`);
    if (response.data.code === 200 && response.data.data && response.data.data.length > 0) {
      const foundUser = response.data.data[0];
      // 如果找到的用户ID与当前编辑的用户ID不同，则视为重复
      if (foundUser.id !== user.value.id) {
        callback(new Error('该用户名已存在，请更换'));
      } else {
        callback(); // 找到的用户是自己，不视为重复
      }
    } else {
      callback(); // 用户名可用
    }
  } catch (error) {
    console.error('检查用户名唯一性请求失败:', error);
    callback(new Error('网络错误，无法检查用户名唯一性'));
  }
};


const editProfileRules = {
  name: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { validator: validateNameUnique, trigger: 'blur' } // 【关键修改】添加用户名唯一性校验
  ],
  phoneNum: [
    { required: true, message: '请输入电话号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  sex: [{ required: true, message: '请选择性别', trigger: 'change' }]
};

const handleEditProfile = () => {
  if (user.value.id === null) {
    ElMessage.warning('用户信息未加载，无法编辑。');
    return;
  }
  // 复制当前用户数据到编辑表单
  Object.assign(editProfileForm, {
    id: user.value.id,
    name: user.value.name,
    phoneNum: user.value.phoneNum,
    sex: String(user.value.sex), // 转换为字符串以匹配radio-button
    account: user.value.account,
    roleId: user.value.roleId
  });
  editProfileDialogVisible.value = true;
};

const cancelEditProfile = () => {
  editProfileDialogVisible.value = false;
  ElMessage.info('已取消编辑资料');
  if (editProfileFormRef.value) {
    editProfileFormRef.value.resetFields();
  }
};

const confirmEditProfile = () => {
  editProfileFormRef.value.validate(async (valid) => {
    if (valid) {
      editProfileLoading.value = true;
      try {
        const dataToSubmit = { ...editProfileForm };
        dataToSubmit.sex = Number(dataToSubmit.sex); // 确保sex字段是数字类型

        delete dataToSubmit.account; // 账号不可修改，不发送
        delete dataToSubmit.roleId; // 角色不可修改，不发送

        const response = await axios.post(`${httpUrl}/user/mod`, dataToSubmit);

        if (response.data.code === 200) {
          ElMessage.success('个人资料更新成功！');
          editProfileDialogVisible.value = false;
          // 更新本地存储的用户信息
          const updatedUser = { ...user.value, ...dataToSubmit };
          updatedUser.sex = dataToSubmit.sex; // 确保 sex 存储为数字
          localStorage.setItem('CurUser', JSON.stringify(updatedUser));
          sessionStorage.setItem('CurUser', JSON.stringify(updatedUser));
          // 刷新当前页面的用户信息显示
          user.value = {
            ...updatedUser,
            sex: String(updatedUser.sex) // 再次转换为字符串以供显示
          };
        } else {
          ElMessage.error(`更新失败: ${response.data.msg || '未知错误'}`);
        }
      } catch (error) {
        console.error('更新个人资料失败:', error);
        ElMessage.error('更新个人资料失败，请稍后重试');
      } finally {
        editProfileLoading.value = false;
      }
    } else {
      ElMessage.warning('请检查表单填写是否完整和正确！');
      return false;
    }
  });
};

// --- 修改密码相关状态 ---
const changePasswordDialogVisible = ref(false);
const changePasswordFormRef = ref(null);
const changePasswordLoading = ref(false);
const changePasswordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmNewPassword: ''
});

const validateConfirmNewPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'));
  } else if (value !== changePasswordForm.newPassword) {
    callback(new Error('两次输入密码不一致'));
  } else {
    callback();
  }
};

const changePasswordRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmNewPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmNewPassword, trigger: 'blur' }
  ]
};

const handleChangePassword = () => {
  if (user.value.id === null) {
    ElMessage.warning('用户信息未加载，无法修改密码。');
    return;
  }
  changePasswordDialogVisible.value = true;
  if (changePasswordFormRef.value) {
    changePasswordFormRef.value.resetFields();
  }
};

const cancelChangePassword = () => {
  changePasswordDialogVisible.value = false;
  ElMessage.info('已取消修改密码');
  if (changePasswordFormRef.value) {
    changePasswordFormRef.value.resetFields();
  }
};

const confirmChangePassword = () => {
  changePasswordFormRef.value.validate(async (valid) => {
    if (valid) {
      changePasswordLoading.value = true;
      try {
        const response = await axios.post(`${httpUrl}/user/mod`, {
          id: user.value.id,
          password: changePasswordForm.newPassword,
          // 如果后端需要旧密码验证，请在这里添加 oldPassword 字段
          // oldPassword: changePasswordForm.oldPassword
        });

        if (response.data.code === 200) {
          ElMessage.success('密码修改成功！请重新登录。');
          changePasswordDialogVisible.value = false;
          // 密码修改成功后，强制用户重新登录以使新密码生效
          // 这通常意味着清除本地存储的用户信息并跳转到登录页
          localStorage.removeItem('CurUser');
          sessionStorage.removeItem('CurUser');
          router.push('/login'); // 确保 router 已导入
        } else {
          ElMessage.error(`修改失败: ${response.data.msg || '未知错误'}`);
        }
      } catch (error) {
        console.error('修改密码失败:', error);
        ElMessage.error('修改密码失败，请稍后重试');
      } finally {
        changePasswordLoading.value = false;
      }
    } else {
      ElMessage.warning('请检查表单填写是否完整和正确！');
      return false;
    }
  });
};


onMounted(() => {
  let storedUser = localStorage.getItem('CurUser');
  if (!storedUser) {
    storedUser = sessionStorage.getItem('CurUser');
  }

  if (storedUser) {
    try {
      const parsedUser = JSON.parse(storedUser);
      if (typeof parsedUser === 'object' && parsedUser !== null) {
        user.value = {
          id: parsedUser.id || null,
          name: parsedUser.name || '加载中...',
          account: parsedUser.account || 'N/A',
          phoneNum: parsedUser.phoneNum || 'N/A',
          sex: String(parsedUser.sex || '0'),
          roleId: parsedUser.roleId !== undefined && parsedUser.roleId !== null ? parsedUser.roleId : -1
        };
      } else {
        console.warn('存储的用户数据无效。');
        user.value = { id: null, name: '数据无效', account: 'N/A', phoneNum: 'N/A', sex: '0', roleId: -1 };
      }
    } catch (e) {
      console.error('解析用户数据失败:', e);
      user.value = { id: null, name: '数据错误', account: 'N/A', phoneNum: 'N/A', sex: '0', roleId: -1 };
    }
  } else {
    user.value = { id: null, name: '访客', account: '未登录', phoneNum: 'N/A', sex: '0', roleId: -1 };
  }

  randomAvatarUrl.value = `https://api.dicebear.com/7.x/adventurer/svg?seed=${Math.random().toString(36).substring(2, 15)}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf`;
});
</script>

<style scoped>
/* 你的原有样式保持不变 */
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s, color 0.3s;
}

.welcome-card {
  width: 90%;
  max-width: 700px;
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  text-align: center;
  margin-bottom: 30px;
  position: relative;
  overflow: hidden;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.welcome-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 8px;
  background: linear-gradient(90deg, #409EFF, #67C23A, #E6A23C, #F56C6C);
}

.avatar-container {
  position: relative;
  width: 140px;
  height: 140px;
  margin: 0 auto 25px;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  position: relative;
  z-index: 2;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.avatar-placeholder:hover .avatar-img {
  transform: scale(1.05);
}

.avatar-border {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  background: linear-gradient(45deg, #409EFF, #67C23A, #E6A23C, #F56C6C);
  z-index: 1;
  animation: rotateBorder 6s linear infinite;
}

.avatar-shadow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  z-index: 0;
}

@keyframes rotateBorder {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.welcome-title {
  font-size: 2.2rem;
  color: #2c3e50;
  margin-bottom: 25px;
  font-weight: 600;
  letter-spacing: 0.5px;
  position: relative;
  display: inline-block;
  transition: color 0.3s;
}

.welcome-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 3px;
  background: linear-gradient(90deg, #409EFF, #67C23A);
  border-radius: 3px;
}

.custom-divider {
  margin: 30px 0;
  background-color: #f0f2f5;
  transition: background-color 0.3s;
}

.info-group {
  margin-bottom: 30px;
  text-align: left;
}

.group-title {
  font-size: 1.3rem;
  color: #34495e;
  margin-bottom: 20px;
  font-weight: 600;
  padding-left: 15px;
  border-left: 4px solid #409EFF;
  line-height: 1;
  letter-spacing: 0.5px;
  transition: color 0.3s, border-left-color 0.3s;
}

/* Element Plus Descriptions 组件的深层样式覆盖 */
:deep(.el-descriptions__label) {
  color: #7f8c8d !important;
  font-weight: 500 !important;
  font-size: 0.95rem;
  transition: color 0.3s;
}

:deep(.el-descriptions__content) {
  color: #2c3e50 !important;
  font-weight: 500 !important;
  font-size: 1.05rem;
  transition: color 0.3s;
}

:deep(.el-descriptions__cell) {
  padding: 16px !important;
  transition: border-color 0.3s;
}

/* 确保 el-descriptions 的边框和背景也适应暗色模式 */
:deep(.el-descriptions__body) {
  background-color: white;
  border-color: #ebeef5;
  transition: background-color 0.3s, border-color 0.3s;
}
:deep(.el-descriptions__table) {
  border-color: #ebeef5;
  transition: border-color 0.3s;
}


.male-icon, .female-icon {
  margin-right: 5px;
}
.male-icon {
  color: #409EFF;
}
.female-icon {
  color: #F56C6C;
}

.gender-tag, .role-tag {
  padding: 0 12px;
  height: 28px;
  line-height: 28px;
  font-size: 0.95rem;
}

.card-actions {
  margin-top: 40px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.action-button {
  padding: 12px 28px;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 25px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.action-button:active {
  transform: translateY(0);
}

/* 从用户管理页面复制的 Dialog 样式 */
.custom-dialog {
  border-radius: 12px;
  overflow: hidden;
  transition: background-color 0.3s, box-shadow 0.3s, border-color 0.3s;
}
:deep(.custom-dialog .el-dialog__header) {
  background: linear-gradient(90deg, #409EFF, #66b1ff);
  margin: 0;
  padding: 16px 24px;
  transition: background 0.3s;
}
:deep(.custom-dialog .el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
  transition: color 0.3s;
}
:deep(.custom-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: white;
  transition: color 0.3s;
}
.dialog-content {
  padding: 20px 24px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
/* 针对编辑资料，如果只有一列的表单项，让它占据两列 */
.form-grid .el-form-item:nth-child(5) { /* 角色 */
  grid-column: span 2;
}
/* 针对修改密码，所有表单项都占据一列 */
.change-password-form .el-form-item {
  grid-column: span 2;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 24px 20px;
}

/* 确保输入框和选择框的样式保持一致 */
:deep(.el-input),
:deep(.el-select),
:deep(.el-input-number) {
  width: 100%;
}

/* ===================================================================== */
/* ======================== 暗黑模式样式 =============================== */
/* ===================================================================== */

html.dark .home-container {
  background: var(--main-content-bg);
  color: var(--text-color);
}

html.dark .home-container .welcome-card {
  background: var(--card-bg);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
}

html.dark .home-container .welcome-card::before {
  background: linear-gradient(90deg, var(--primary-color), #6B78E6, #FF9800, #EF5350);
}

html.dark .home-container .welcome-title {
  color: var(--text-color);
}

html.dark .home-container .welcome-title::after {
  background: linear-gradient(90deg, var(--primary-color), #6B78E6);
}

html.dark .home-container .custom-divider {
  background-color: var(--border-color);
}

html.dark .home-container .info-group .group-title {
  color: var(--text-color);
  border-left-color: var(--primary-color);
}

/* Element Plus Descriptions 组件的暗黑模式样式覆盖 */
html.dark :deep(.el-descriptions__body) {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}
html.dark :deep(.el-descriptions__label) {
  background-color: #2D2D2D !important;
  color: var(--text-color) !important;
}
html.dark :deep(.el-descriptions__content) {
  background-color: #1E1E1E !important;
  color: var(--text-color) !important;
}
html.dark :deep(.el-descriptions__cell) {
  border-color: var(--border-color);
}
html.dark :deep(.el-descriptions__table) {
  border-color: var(--border-color);
}

html.dark .custom-dialog {
  background-color: var(--card-bg);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.5);
  border-color: var(--border-color);
}
html.dark :deep(.custom-dialog .el-dialog__header) {
  background: linear-gradient(90deg, var(--primary-color), #6B78E6);
}
html.dark :deep(.custom-dialog .el-dialog__title) {
  color: white;
}
html.dark :deep(.custom-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: white;
}
html.dark :deep(.custom-dialog .el-form-item__label) {
  color: var(--secondary-text-color);
}
html.dark :deep(.custom-dialog .el-input__inner),
html.dark :deep(.custom-dialog .el-textarea__inner) {
  background-color: #333333;
  border-color: var(--border-color);
  color: var(--text-color);
}
html.dark :deep(.custom-dialog .el-input__wrapper) {
  background-color: #333333;
}
html.dark :deep(.custom-dialog .el-input__prefix) {
  color: var(--secondary-text-color);
}
html.dark :deep(.custom-dialog .el-radio-button__inner) {
  background-color: #3A3A3A;
  color: var(--text-color);
  border-color: var(--border-color);
}
html.dark :deep(.custom-dialog .el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}
html.dark :deep(.custom-dialog .el-select .el-input__inner) {
  background-color: #333333;
  color: var(--text-color);
  border-color: var(--border-color);
}
</style>