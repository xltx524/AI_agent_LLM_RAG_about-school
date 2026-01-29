<script setup>
import { ref, onMounted, getCurrentInstance, reactive } from "vue";
import axios from "axios";
import { Search, Plus, Edit, Delete, More, Refresh, User, Setting, Key, Lock, Phone, Warning, InfoFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus'; // 移除 ElTooltip 导入
import { ElConfigProvider } from 'element-plus';
import zhCn from 'element-plus/dist/locale/zh-cn.mjs';

const { proxy } = getCurrentInstance();
const httpUrl = proxy.$httpUrl;
const tableData = ref([]);
const loading = ref(false);
const searchQuery = ref("");
const selectedRole = ref("");

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
});

// --- 添加用户相关状态 ---
const addDialogVisible = ref(false);
const addFormRef = ref(null);
const addLoading = ref(false);
const addForm = reactive({
  name: '',
  account: '',
  password: '',
  confirmPassword: '',
  sex: 1,
  age: null,
  phoneNum: '',
  roleId: 2,
  isValid: 'Y' // 默认设置为有效
});

// --- 编辑用户相关状态 ---
const editDialogVisible = ref(false);
const editFormRef = ref(null);
const editLoading = ref(false);
const editForm = reactive({
  id: null, // 必须有ID来区分当前编辑的用户
  name: '',
  account: '',
  password: '',
  confirmPassword: '',
  sex: 1,
  age: null,
  phoneNum: '',
  roleId: 2,
  isValid: 'Y'
});

// --- 删除用户相关状态 ---
const deleteDialogVisible = ref(false);
const currentDeleteUser = ref(null);
const deleteLoading = ref(false);

// --- 切换用户状态相关状态 ---
const toggleStatusDialogVisible = ref(false);
const currentToggleUser = ref(null);
const toggleTargetStatus = ref('');
const toggleLoading = ref(false);

// --- 查看用户详情相关状态 ---
const viewDialogVisible = ref(false);
const currentViewUser = ref(null); // 用于存储当前查看的用户信息

// 检查账号唯一性 (用于添加用户，以及编辑时如果账号可修改也可复用)
const validateAccountUnique = async (rule, value, callback) => {
  if (!value) {
    if (editDialogVisible.value && value === editForm.account) {
      return callback();
    }
    return callback(new Error('请输入账号'));
  }
  if (value.length < 3 || value.length > 15) {
    return callback();
  }
  try {
    const response = await axios.get(`${httpUrl}/user/findByNo?account=${value}`);
    if (response.data.code === 200 && response.data.data && response.data.data.length > 0) {
      const foundUser = response.data.data[0];
      if (editDialogVisible.value && foundUser.id === editForm.id) {
        callback();
      } else {
        callback(new Error('该账号已存在，请更换'));
      }
    } else {
      callback();
    }
  } catch (error) {
    console.error('检查账号唯一性请求失败:', error);
    callback(new Error('网络错误，无法检查账号唯一性'));
  }
};

// 【修改】检查用户名唯一性 (用于添加和编辑用户)
const validateNameUnique = async (rule, value, callback) => {
  if (!value) {
    if (editDialogVisible.value && value === editForm.name) {
      return callback();
    }
    return callback(new Error('请输入用户名'));
  }
  if (value.length < 2 || value.length > 20) {
    return callback();
  }
  try {
    const response = await axios.get(`${httpUrl}/user/findByName?name=${value}`);
    if (response.data.code === 200 && response.data.data && response.data.data.length > 0) {
      const foundUser = response.data.data[0];
      if (editDialogVisible.value && foundUser.id === editForm.id) {
        callback();
      } else {
        callback(new Error('该用户名已存在，请更换'));
      }
    } else {
      callback();
    }
  } catch (error) {
    console.error('检查用户名唯一性请求失败:', error);
    callback(new Error('网络错误，无法检查用户名唯一性'));
  }
};


// 添加用户的验证规则
const addRules = {
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
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请再次输入密码'));
        } else if (value !== addForm.password) {
          callback(new Error('两次输入密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  sex: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age: [
    { required: true, message: '请输入年龄', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value && value !== 0) return callback();
        const numValue = Number(value);
        if (isNaN(numValue)) callback(new Error('年龄必须为数字'));
        else if (numValue < 1 || numValue > 120) callback(new Error('年龄必须在1到120之间'));
        else callback();
      },
      trigger: 'blur'
    }
  ],
  phoneNum: [
    { required: true, message: '请输入电话号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  roleId: [{ required: true, message: '请选择角色', trigger: 'change' }]
};

// 【修改】编辑用户的验证规则
const editRules = {
  name: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { validator: validateNameUnique, trigger: 'blur' }
  ],
  password: [
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    {
      validator: (rule, value, callback) => {
        if (editForm.password && value !== editForm.password) {
          callback(new Error('两次输入密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  sex: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age: [
    { required: true, message: '请输入年龄', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value && value !== 0) return callback();
        const numValue = Number(value);
        if (isNaN(numValue)) callback(new Error('年龄必须为数字'));
        else if (numValue < 1 || numValue > 120) callback(new Error('年龄必须在1到120之间'));
        else callback();
      },
      trigger: 'blur'
    }
  ],
  phoneNum: [
    { required: true, message: '请输入电话号码', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  roleId: [{ required: true, message: '请选择角色', trigger: 'change' }]
};


const roleOptions = [
  { value: 0, label: '超级管理员' },
  { value: 1, label: '管理员' },
  { value: 2, label: '用户' }
];

const theme = ref('light');

const loadUserData = () => {
  loading.value = true;
  axios.post(`${httpUrl}/user/listPageC1`, {
    pageNum: pagination.currentPage,
    pageSize: pagination.pageSize,
    param: {
      searchText: searchQuery.value,
      roleId: selectedRole.value === '' ? null : selectedRole.value
    }
  })
      .then(response => {
        if (response.status === 200 && response.data.code === 200) {
          tableData.value = response.data.data || [];
          pagination.total = response.data.total || 0;
        } else {
          ElMessage.error(`获取数据失败: ${response.data.msg || '未知错误'}`);
        }
      })
      .catch(error => {
        console.error('请求失败:', error);
        ElMessage.error('网络请求失败，请稍后重试');
      })
      .finally(() => {
        loading.value = false;
      });
};

const handlePageChange = (page) => {
  pagination.currentPage = page;
  loadUserData();
};

const handleSearch = () => {
  pagination.currentPage = 1;
  loadUserData();
};

const handleRoleChange = () => {
  pagination.currentPage = 1;
  loadUserData();
};

const handleEdit = (row) => {
  Object.assign(editForm, row);
  editForm.password = '';
  editForm.confirmPassword = '';
  editDialogVisible.value = true;
};

const cancelEditUser = () => {
  editDialogVisible.value = false;
  ElMessage.info('已取消编辑');
};

const confirmEditUser = () => {
  editFormRef.value.validate(async (valid) => {
    if (valid) {
      editLoading.value = true;
      try {
        const dataToSubmit = { ...editForm };
        if (dataToSubmit.password === '') {
          delete dataToSubmit.password;
          delete dataToSubmit.confirmPassword;
        }
        const response = await axios.post(`${httpUrl}/user/mod`, dataToSubmit);
        if (response.data.code === 200) {
          ElMessage.success('用户信息更新成功！');
          editDialogVisible.value = false;
          loadUserData();
        } else {
          ElMessage.error(`更新失败: ${response.data.msg || '未知错误'}`);
        }
      } catch (error) {
        console.error('更新用户失败:', error);
        ElMessage.error('更新用户失败，请稍后重试');
      } finally {
        editLoading.value = false;
      }
    } else {
      ElMessage.warning('请检查表单填写是否完整和正确！');
      return false;
    }
  });
};


const handleAdd = () => {
  addDialogVisible.value = true;
  if (addFormRef.value) {
    addFormRef.value.resetFields();
    addForm.age = null;
    addForm.isValid = 'Y';
  }
};

const cancelAddUser = () => {
  if (addFormRef.value) {
    addFormRef.value.resetFields();
    addForm.age = null;
    addForm.isValid = 'Y';
  }
  addDialogVisible.value = false;
  ElMessage.info('已取消添加用户');
};

const confirmAddUser = () => {
  addFormRef.value.validate(async (valid) => {
    if (valid) {
      addLoading.value = true;
      try {
        const response = await axios.post(`${httpUrl}/user/save`, addForm);
        if (response.data.code === 200) {
          ElMessage.success('用户添加成功！');
          addDialogVisible.value = false;
          loadUserData();
          addFormRef.value.resetFields();
          addForm.age = null;
          addForm.isValid = 'Y';
        } else {
          ElMessage.error(`添加失败: ${response.data.msg}`);
        }
      } catch (error) {
        console.error('添加用户失败:', error);
        ElMessage.error('添加用户失败，请稍后重试');
      } finally {
        addLoading.value = false;
      }
    } else {
      ElMessage.warning('请检查表单填写是否完整和正确！');
      return false;
    }
  });
};

const handleDelete = (row) => {
  currentDeleteUser.value = row;
  deleteDialogVisible.value = true;
};

const cancelDeleteUser = () => {
  deleteDialogVisible.value = false;
  currentDeleteUser.value = null;
  ElMessage.info('已取消删除操作');
};

const confirmDeleteUser = async () => {
  if (currentDeleteUser.value) {
    deleteLoading.value = true;
    try {
      const response = await axios.get(`${httpUrl}/user/delete?id=${currentDeleteUser.value.id}`);
      if (response.data.code === 200) {
        ElMessage.success(`用户 ${currentDeleteUser.value.name} 已删除`);
        loadUserData();
      } else {
        ElMessage.error(`删除失败: ${response.data.msg || '未知错误'}`);
      }
    } catch (error) {
      console.error('删除用户失败:', error);
      ElMessage.error('删除用户失败，请稍后重试');
    } finally {
      deleteLoading.value = false;
      deleteDialogVisible.value = false;
      currentDeleteUser.value = null;
    }
  }
};

const handleToggleStatus = (row, status) => {
  currentToggleUser.value = row;
  toggleTargetStatus.value = status;
  toggleStatusDialogVisible.value = true;
};

const cancelToggleStatus = () => {
  toggleStatusDialogVisible.value = false;
  currentToggleUser.value = null;
  toggleTargetStatus.value = '';
  ElMessage.info('已取消操作');
};

const confirmToggleStatus = async () => {
  if (currentToggleUser.value) {
    toggleLoading.value = true;
    try {
      const response = await axios.post(`${httpUrl}/user/toggleStatus`, {
        id: currentToggleUser.value.id,
        isValid: toggleTargetStatus.value
      });

      if (response.data.code === 200) {
        ElMessage.success(`用户 ${currentToggleUser.value.name} 已${toggleTargetStatus.value === 'N' ? '禁用' : '启用'}`);
        loadUserData();
      } else {
        ElMessage.error(`操作失败: ${response.data.msg || '未知错误'}`);
      }
    } catch (error) {
      console.error('切换用户状态失败:', error);
      ElMessage.error('切换用户状态失败，请稍后重试');
    } finally {
      toggleLoading.value = false;
      toggleStatusDialogVisible.value = false;
      currentToggleUser.value = null;
      toggleTargetStatus.value = '';
    }
  }
};

const handleViewDetails = (row) => {
  currentViewUser.value = { ...row };
  viewDialogVisible.value = true;
};

const cancelViewDetails = () => {
  viewDialogVisible.value = false;
  currentViewUser.value = null;
};

const refreshData = () => {
  searchQuery.value = "";
  selectedRole.value = "";
  loadUserData();
  ElMessage.success('数据已刷新');
};

onMounted(() => {
  loadUserData();
});
</script>

<template>
  <div class="user-management-container" :class="{'dark-mode': theme === 'dark'}">
    <!-- 页面标题和搜索区 -->
    <div class="page-header">
      <div class="title-section">
        <h1>用户管理</h1>
        <p class="subtitle">管理系统用户账号、权限及个人信息</p>
      </div>

      <div class="search-section">
        <div class="search-filters">
          <el-input
              v-model="searchQuery"
              v-loading="loading"
              placeholder="搜索用户名、账号或电话"
              class="search-input"
              @keyup.enter="handleSearch"
              size="large"
          >
            <template #prefix>
              <el-icon :size="18">
                <Search/>
              </el-icon>
            </template>
          </el-input>

          <el-select
              v-model="selectedRole"
              placeholder="请选择角色"
              clearable
              @change="handleRoleChange"
              size="large"
              class="role-select"
          >
            <el-option label="全部" value="" />
            <el-option
                v-for="role in roleOptions"
                :key="role.value"
                :label="role.label"
                :value="role.value"
            />
          </el-select>

          <el-button @click="handleSearch" type="primary" size="large" class="search-button">
            搜索
          </el-button>
        </div>

        <div class="action-buttons-group">
          <el-button @click="handleAdd" type="primary" class="add-button" size="large">
            <el-icon :size="18">
              <Plus/>
            </el-icon>
            添加用户
          </el-button>

          <el-button type="info" plain @click="refreshData" size="large">
            <el-icon :size="18">
              <Refresh/>
            </el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 添加用户 Dialog -->
    <el-dialog
        v-model="addDialogVisible"
        title="添加新用户"
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
            :model="addForm"
            :rules="addRules"
            ref="addFormRef"
        >
          <div class="form-grid">
            <el-form-item label="用户名" prop="name">
              <el-input
                  v-model="addForm.name"
                  placeholder="请输入用户名"
                  clearable
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="账号" prop="account">
              <el-input
                  v-model="addForm.account"
                  placeholder="请输入账号"
                  clearable
              >
                <template #prefix>
                  <el-icon><Key /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                  v-model="addForm.password"
                  type="password"
                  placeholder="请输入密码"
                  show-password
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                  v-model="addForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入密码"
                  show-password
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="性别" prop="sex">
              <el-radio-group v-model="addForm.sex">
                <el-radio-button :label="1">男</el-radio-button>
                <el-radio-button :label="2">女</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="年龄" prop="age">
              <el-input-number
                  v-model="addForm.age"
                  :min="1"
                  :max="120"
                  placeholder="请输入年龄"
                  style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="电话" prop="phoneNum">
              <el-input
                  v-model="addForm.phoneNum"
                  placeholder="请输入电话号码"
                  clearable
              >
                <template #prefix>
                  <el-icon><Phone /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="角色" prop="roleId">
              <el-select
                  v-model="addForm.roleId"
                  placeholder="请选择角色"
                  clearable
                  style="width: 100%"
              >
                <el-option
                    v-for="role in roleOptions"
                    :key="role.value"
                    :label="role.label"
                    :value="role.value"
                />
              </el-select>
            </el-form-item>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelAddUser" size="large">取消</el-button>
          <el-button
              type="primary"
              @click="confirmAddUser"
              size="large"
              :loading="addLoading"
          >
            确认添加
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑用户 Dialog -->
    <el-dialog
        v-model="editDialogVisible"
        title="编辑用户信息"
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
            :model="editForm"
            :rules="editRules"
            ref="editFormRef"
        >
          <div class="form-grid">
            <el-form-item label="用户名" prop="name">
              <el-input v-model="editForm.name" placeholder="请输入用户名" clearable>
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="账号" prop="account">
              <el-input v-model="editForm.account" placeholder="账号不可修改" disabled>
                <template #prefix><el-icon><Key /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="新密码" prop="password">
              <el-input
                  v-model="editForm.password"
                  type="password"
                  placeholder="留空则不修改密码"
                  show-password
              >
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input
                  v-model="editForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入新密码"
                  show-password
              >
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="性别" prop="sex">
              <el-radio-group v-model="editForm.sex">
                <el-radio-button :label="1">男</el-radio-button>
                <el-radio-button :label="2">女</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="年龄" prop="age">
              <el-input-number
                  v-model="editForm.age"
                  :min="1"
                  :max="120"
                  placeholder="请输入年龄"
                  style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="电话" prop="phoneNum">
              <el-input v-model="editForm.phoneNum" placeholder="请输入电话号码" clearable>
                <template #prefix><el-icon><Phone /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-form-item label="角色" prop="roleId">
              <el-select v-model="editForm.roleId" placeholder="请选择角色" style="width: 100%">
                <el-option
                    v-for="role in roleOptions"
                    :key="role.value"
                    :label="role.label"
                    :value="role.value"
                />
              </el-select>
            </el-form-item>
          </div>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelEditUser" size="large">取消</el-button>
          <el-button
              type="primary"
              @click="confirmEditUser"
              size="large"
              :loading="editLoading"
          >
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>


    <!-- 数据表格 -->
    <div class="table-container">
      <el-card shadow="hover" class="table-card">
        <el-scrollbar>
          <el-table
              :data="tableData"
              style="width: 100%"
              v-loading="loading"
              border
              stripe
              highlight-current-row
          >
            <el-table-column prop="id" label="ID" width="80" align="center"/>
            <el-table-column prop="account" label="账号" min-width="120" show-overflow-tooltip/>
            <el-table-column prop="name" label="用户名" min-width="120" show-overflow-tooltip/>
            <el-table-column prop="age" label="年龄" width="80" align="center"/>
            <el-table-column label="性别" width="100" align="center">
              <template #default="scope">
                <el-tag
                    :type="scope.row.sex === 1 ? 'info' : 'success'"
                    effect="light"
                    round
                    size="large"
                >
                  {{ scope.row.sex === 1 ? '男' : '女' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="角色" width="160" align="center">
              <template #default="scope">
                <el-tag
                    :type="scope.row.roleId === 0 ? 'danger' : (scope.row.roleId === 1 ? 'primary' : 'success')"
                    effect="plain"
                    size="large"
                >
                  <el-icon v-if="scope.row.roleId === 0" :size="16">
                    <Key/>
                  </el-icon>
                  <el-icon v-else-if="scope.row.roleId === 1" :size="16">
                    <Setting/>
                  </el-icon>
                  <el-icon v-else :size="16">
                    <User/>
                  </el-icon>
                  {{ scope.row.roleId === 0 ? '超级管理员' : (scope.row.roleId === 1 ? '管理员' : '用户') }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="phoneNum" label="电话" min-width="140" show-overflow-tooltip/>

            <el-table-column label="状态" width="100" align="center">
              <template #default="scope">
                <el-tag
                    :type="scope.row.isValid === 'Y' ? 'success' : 'danger'"
                    effect="light"
                    round
                    size="large"
                >
                  {{ scope.row.isValid === 'Y' ? '正常' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <div class="action-buttons">
                  <el-tooltip content="编辑用户" placement="top">
                    <div class="action-button edit" @click="handleEdit(scope.row)">
                      <el-icon :size="18">
                        <Edit/>
                      </el-icon>
                    </div>
                  </el-tooltip>
                  <el-tooltip content="删除用户" placement="top">
                    <div class="action-button delete" @click="handleDelete(scope.row)">
                      <el-icon :size="18">
                        <Delete/>
                      </el-icon>
                    </div>
                  </el-tooltip>
                  <el-dropdown trigger="click">
                    <el-tooltip content="更多操作" placement="top">
                      <div class="action-button more">
                        <el-icon :size="18">
                          <More/>
                        </el-icon>
                      </div>
                    </el-tooltip>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="handleViewDetails(scope.row)">
                          <el-icon :size="16">
                            <InfoFilled/>
                          </el-icon>
                          <span class="dropdown-text">查看详情</span>
                        </el-dropdown-item>
                        <el-dropdown-item>
                          <el-icon :size="16">
                            <Key/>
                          </el-icon>
                          <span class="dropdown-text">重置密码</span>
                        </el-dropdown-item>
                        <el-dropdown-item divided
                                          v-if="scope.row.isValid === 'Y'"
                                          @click="handleToggleStatus(scope.row, 'N')"
                        >
                          <el-icon :size="16">
                            <Warning/>
                          </el-icon>
                          <span class="dropdown-text" style="color: #f56c6c;">禁用账号</span>
                        </el-dropdown-item>
                        <el-dropdown-item divided
                                          v-else
                                          @click="handleToggleStatus(scope.row, 'Y')"
                        >
                          <el-icon :size="16">
                            <Warning/>
                          </el-icon>
                          <span class="dropdown-text" style="color: #67C23A;">启用账号</span>
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-scrollbar>

        <!-- 删除用户 Dialog -->
        <el-dialog
            v-model="deleteDialogVisible"
            title="删除用户确认"
            width="450px"
            :show-close="false"
            class="danger-dialog"
            center
            :close-on-click-modal="false"
        >
          <div class="delete-dialog-content">
            <div class="delete-icon">
              <el-icon color="#F56C6C" :size="60"><Warning /></el-icon>
            </div>
            <div class="delete-text">
              <h3>确定要删除用户 "<span class="highlight">{{ currentDeleteUser?.name }}</span>" 吗？</h3>
              <p class="warning-text">此操作将永久删除该用户的所有数据，且无法恢复！</p>
              <div class="user-info" v-if="currentDeleteUser">
                <p><span class="info-label">账号:</span> {{ currentDeleteUser.account }}</p>
                <p><span class="info-label">角色:</span>
                  <el-tag :type="currentDeleteUser.roleId === 0 ? 'danger' : (currentDeleteUser.roleId === 1 ? 'primary' : 'success')">
                    {{ currentDeleteUser.roleId === 0 ? '超级管理员' : (currentDeleteUser.roleId === 1 ? '管理员' : '用户') }}
                  </el-tag>
                </p>
              </div>
            </div>
          </div>
          <template #footer>
            <div class="dialog-footer">
              <el-button @click="cancelDeleteUser" size="large">取消</el-button>
              <el-button
                  type="danger"
                  @click="confirmDeleteUser"
                  size="large"
                  :loading="deleteLoading"
              >
                确认删除
              </el-button>
            </div>
          </template>
        </el-dialog>

        <!-- 切换用户状态 Dialog -->
        <el-dialog
            v-model="toggleStatusDialogVisible"
            :title="toggleTargetStatus === 'N' ? '禁用用户确认' : '启用用户确认'"
            width="450px"
            :show-close="false"
            :class="toggleTargetStatus === 'N' ? 'danger-dialog' : 'success-dialog'"
            center
            :close-on-click-modal="false"
        >
          <div class="delete-dialog-content">
            <div class="delete-icon">
              <el-icon :color="toggleTargetStatus === 'N' ? '#F56C6C' : '#67C23A'" :size="60">
                <Warning/>
              </el-icon>
            </div>
            <div class="delete-text">
              <h3>确定要{{ toggleTargetStatus === 'N' ? '禁用' : '启用' }}用户 "<span class="highlight">{{ currentToggleUser?.name }}</span>" 吗？</h3>
              <p :class="toggleTargetStatus === 'N' ? 'warning-text' : 'info-text'">
                {{ toggleTargetStatus === 'N' ? '禁用后该用户将无法登录系统！' : '启用后该用户将可以正常登录系统。' }}
              </p>
              <div class="user-info" v-if="currentToggleUser">
                <p><span class="info-label">账号:</span> {{ currentToggleUser.account }}</p>
                <p><span class="info-label">角色:</span>
                  <el-tag :type="currentToggleUser.roleId === 0 ? 'danger' : (currentToggleUser.roleId === 1 ? 'primary' : 'success')">
                    {{ currentToggleUser.roleId === 0 ? '超级管理员' : (currentToggleUser.roleId === 1 ? '管理员' : '用户') }}
                  </el-tag>
                </p>
                <p><span class="info-label">当前状态:</span>
                  <el-tag :type="currentToggleUser.isValid === 'Y' ? 'success' : 'danger'">
                    {{ currentToggleUser.isValid === 'Y' ? '正常' : '禁用' }}
                  </el-tag>
                </p>
              </div>
            </div>
          </div>
          <template #footer>
            <div class="dialog-footer">
              <el-button @click="cancelToggleStatus" size="large">取消</el-button>
              <el-button
                  :type="toggleTargetStatus === 'N' ? 'danger' : 'success'"
                  @click="confirmToggleStatus"
                  size="large"
                  :loading="toggleLoading"
              >
                确认{{ toggleTargetStatus === 'N' ? '禁用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-dialog>

        <!-- 【修改后】查看用户详情 Dialog -->
        <el-dialog
            v-model="viewDialogVisible"
            title="用户详情"
            width="750px"
            :show-close="false"
            class="custom-dialog"
            center
            :close-on-click-modal="false"
        >
          <div class="dialog-content" v-if="currentViewUser">
            <div class="view-details-container">
              <!-- 左侧：身份卡 -->
              <div class="details-left">
                <el-avatar :size="100" :icon="User" />
                <h3 class="user-name">{{ currentViewUser.name }}</h3>
                <div class="user-account">
                  <el-icon><Key /></el-icon>
                  <span>{{ currentViewUser.account }}</span>
                </div>
              </div>
              <!-- 右侧：详细信息 -->
              <div class="details-right">
                <el-descriptions
                    :column="2"
                    border
                    size="large"
                >
                  <el-descriptions-item label="ID">{{ currentViewUser.id }}</el-descriptions-item>
                  <el-descriptions-item label="性别">
                    <el-tag :type="currentViewUser.sex === 1 ? 'info' : 'success'" effect="light" round>
                      {{ currentViewUser.sex === 1 ? '男' : '女' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="年龄">{{ currentViewUser.age }}</el-descriptions-item>
                  <el-descriptions-item label="电话号码">{{ currentViewUser.phoneNum }}</el-descriptions-item>
                  <el-descriptions-item label="角色" :span="2">
                    <el-tag
                        :type="currentViewUser.roleId === 0 ? 'danger' : (currentViewUser.roleId === 1 ? 'primary' : 'success')"
                        effect="plain"
                    >
                      <el-icon v-if="currentViewUser.roleId === 0"><Key /></el-icon>
                      <el-icon v-else-if="currentViewUser.roleId === 1"><Setting /></el-icon>
                      <el-icon v-else><User /></el-icon>
                      {{ currentViewUser.roleId === 0 ? '超级管理员' : (currentViewUser.roleId === 1 ? '管理员' : '用户') }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="currentViewUser.isValid === 'Y' ? 'success' : 'danger'" effect="light" round>
                      {{ currentViewUser.isValid === 'Y' ? '正常' : '禁用' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="创建时间" v-if="currentViewUser.createTime">{{ currentViewUser.createTime }}</el-descriptions-item>
                  <el-descriptions-item label="更新时间" v-if="currentViewUser.updateTime" :span="2">{{ currentViewUser.updateTime }}</el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </div>
          <template #footer>
            <div class="dialog-footer">
              <el-button type="primary" @click="cancelViewDetails" size="large">关闭</el-button>
            </div>
          </template>
        </el-dialog>


        <!-- 分页 -->
        <div class="pagination-container">
          <el-config-provider :locale="zhCn">
            <el-pagination
                v-model:current-page="pagination.currentPage"
                v-model:page-size="pagination.pageSize"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="pagination.total"
                @size-change="loadUserData"
                @current-change="handlePageChange"
                background
                :default-page-size="10"
                style="font-size: 15px;"
            />
          </el-config-provider>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
/* 你的原有样式保持不变 */
:root {
  --bg-color: #f5f7fa;
  --table-container-bg: #ffffff;
  --table-header-bg: #f5f7fa;
  --table-row-bg: #ffffff;
  --table-border-color: #ebeef5;
  --text-color-primary: #303133;
  --text-color-secondary: #606266;
  --search-bg: #ffffff;
  --search-text-color: #303133;
  --pagination-bg: #ffffff;
  --pagination-text-color: #606266;
  --table-row-hover-bg: #ecf5ff;
}
.dark-mode {
  --bg-color: #121212;
  --table-container-bg: #1e1e1e;
  --table-header-bg: #1e1e1e;
  --table-row-bg: #2d2d2d;
  --table-border-color: #3a3a3a;
  --text-color-primary: #e0e0e0;
  --text-color-secondary: #a0a0a0;
  --search-bg: #2d2d2d;
  --search-text-color: #e0e0e0;
  --pagination-bg: #2d2d2d;
  --pagination-text-color: #e0e0e0;
  --table-row-hover-bg: #1a3a5a;
}
.user-management-container {
  padding: 24px;
  background-color: var(--bg-color);
  min-height: calc(100vh - 60px);
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  color: var(--text-color-primary);
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 20px;
}
.title-section h1 {
  font-size: 28px;
  color: var(--text-color-primary);
  margin: 0 0 10px 0;
  font-weight: 600;
}
.subtitle {
  color: var(--text-color-secondary);
  font-size: 16px;
  margin: 0;
}
.search-section {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.search-filters {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.search-input {
  width: 280px;
  font-size: 16px;
  background-color: var(--search-bg);
  color: var(--search-text-color);
}
.role-select {
  width: 140px;
  font-size: 16px;
  background-color: var(--search-bg);
  color: var(--search-text-color);
}
.search-button {
  height: 40px;
  font-size: 16px;
}
.search-input::placeholder {
  color: var(--text-color-secondary);
}
.action-buttons-group {
  display: flex;
  gap: 12px;
  align-items: center;
}
.add-button {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  height: 40px;
}
.table-container {
  margin-bottom: 24px;
}
.table-card {
  border-radius: 10px;
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08);
  padding: 8px;
  background-color: var(--table-container-bg);
}
.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.action-button {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
.action-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);
}
.action-button.edit {
  background-color: #409EFF;
}
.action-button.edit:hover {
  background-color: #66b1ff;
}
.action-button.delete {
  background-color: #F56C6C;
}
.action-button.delete:hover {
  background-color: #f78989;
}
.action-button.more {
  background-color: #909399;
}
.action-button.more:hover {
  background-color: #a6a9ad;
}
.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
:deep(.el-dropdown-menu__item) {
  font-size: 16px;
  padding: 10px 20px;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 8px;
}
.dropdown-text {
  font-size: 16px;
}
:deep(.el-table__header-wrapper th) {
  background-color: var(--table-header-bg) !important;
  color: var(--text-color-primary);
}
:deep(.el-table tr) {
  background-color: var(--table-row-bg);
  color: var(--text-color-primary);
}
:deep(.el-table__body tr:hover > td) {
  background-color: var(--table-row-hover-bg) !important;
}
:deep(.el-table__border, .el-table__cell) {
  border-color: var(--table-border-color);
}
:deep(.el-pagination) {
  background-color: var(--pagination-bg);
  color: var(--pagination-text-color);
}
:deep(.el-pager li) {
  color: var(--pagination-text-color);
}
@media (max-width: 1024px) {
  .search-section {
    flex-direction: column;
    align-items: flex-start;
  }
  .search-filters {
    width: 100%;
  }
  .action-buttons-group {
    margin-top: 12px;
  }
}
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .search-section {
    width: 100%;
  }
  .search-input {
    width: 100%;
  }
  .role-select {
    width: 100%;
  }
  .search-filters {
    flex-direction: column;
    width: 100%;
  }
  .search-button {
    width: 100%;
  }
  .action-buttons-group {
    width: 100%;
    justify-content: space-between;
  }
  .action-buttons {
    gap: 10px;
  }
  .action-button {
    width: 38px;
    height: 38px;
  }
}
.custom-dialog {
  border-radius: 12px;
  overflow: hidden;
}
:deep(.custom-dialog .el-dialog__header) {
  background: linear-gradient(90deg, #409EFF, #66b1ff);
  margin: 0;
  padding: 16px 24px;
}
:deep(.custom-dialog .el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}
:deep(.custom-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: white;
}
.dialog-content {
  padding: 20px 24px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.danger-dialog {
  border-radius: 12px;
  overflow: hidden;
}
:deep(.danger-dialog .el-dialog__header) {
  background: linear-gradient(90deg, #F56C6C, #f78989);
  margin: 0;
  padding: 16px 24px;
}
:deep(.danger-dialog .el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}
:deep(.danger-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: white;
}
.delete-dialog-content {
  display: flex;
  align-items: center;
  padding: 24px;
  gap: 24px;
}
.delete-icon {
  flex-shrink: 0;
}
.delete-text {
  flex: 1;
}
.delete-text h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #303133;
}
.highlight {
  color: #F56C6C; /* 默认红色，用于禁用/删除 */
  font-weight: 600;
}
.warning-text {
  color: #F56C6C;
  margin: 12px 0;
  font-size: 14px;
}
.user-info {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e0e0e0;
}
.user-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}
.info-label {
  display: inline-block;
  width: 60px;
  color: #909399;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 24px 20px;
}

/* 启用操作对话框的样式 */
.success-dialog {
  border-radius: 12px;
  overflow: hidden;
}
:deep(.success-dialog .el-dialog__header) {
  background: linear-gradient(90deg, #67C23A, #85ce61);
  margin: 0;
  padding: 16px 24px;
}
:deep(.success-dialog .el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}
:deep(.success-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: white;
}
.info-text {
  color: #67C23A;
  margin: 12px 0;
  font-size: 14px;
}
.success-dialog .highlight {
  color: #67C23A;
}


/* === 新增和修改：查看详情弹窗样式 === */
.view-details-container {
  display: flex;
  gap: 30px;
}

.details-left {
  flex-shrink: 0;
  width: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-right: 30px;
  border-right: 1px solid var(--table-border-color);
}

.user-name {
  font-size: 22px;
  font-weight: 600;
  margin-top: 16px;
  margin-bottom: 8px;
  color: var(--text-color-primary);
}

.user-account {
  font-size: 14px;
  color: var(--text-color-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.details-right {
  flex: 1;
  min-width: 0; /* 防止 flex 溢出 */
}

/* 调整 el-descriptions 内部样式 */
:deep(.el-descriptions__body) {
  background-color: transparent; /* 使其继承父容器背景 */
}
:deep(.el-descriptions__cell) {
  padding: 10px 12px;
}
:deep(.el-descriptions__label.is-bordered-label) {
  background-color: var(--table-header-bg);
  font-weight: 500;
  color: var(--text-color-secondary);
  width: 100px; /* 统一标签宽度 */
}
:deep(.el-descriptions__content.is-bordered-content) {
  background-color: var(--table-row-bg);
  color: var(--text-color-primary);
  font-weight: 500;
}
</style>