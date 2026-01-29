<template>
  <el-container class="knowledge-base-management">
    <!-- 页面顶部操作栏 -->
    <el-header class="header-toolbar">
      <div class="title">知识库管理</div>
      <div class="controls">
        <!-- 搜索框 -->
        <el-input
            v-model="searchKeyword"
            placeholder="搜索知识标题或内容"
            clearable
            @clear="handleFilterChange"
            @keyup.enter="handleFilterChange"
            class="search-input"
        >
          <template #append>
            <!-- 【修改】点击按钮也应触发筛选/搜索逻辑 -->
            <el-button :icon="Search" @click="handleFilterChange"></el-button>
          </template>
        </el-input>

        <!-- 知识类型筛选器 -->
        <el-select
            v-model="knowledgeTypeFilter"
            placeholder="筛选知识类型"
            clearable
            @change="handleFilterChange"
            class="filter-select"
        >
          <el-option
              v-for="item in knowledgeTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
          ></el-option>
        </el-select>

        <!-- 处理状态筛选器 -->
        <el-select
            v-model="knowledgeStatusFilter"
            placeholder="筛选处理状态"
            clearable
            @change="handleFilterChange"
            class="filter-select"
        >
          <el-option
              v-for="item in knowledgeStatuses"
              :key="item.value"
              :label="item.label"
              :value="item.value"
          ></el-option>
        </el-select>

        <!-- 添加知识按钮 -->
        <el-button type="primary" :icon="Plus" @click="openAddDialog" class="add-button">
          添加知识
        </el-button>
        <!-- 重建知识库索引按钮 -->
        <el-button
            type="warning"
            :icon="Refresh"
            @click="rebuildIndex"
            :loading="rebuildingIndexLoading"
            class="rebuild-button"
        >
          重建知识库索引
        </el-button>
      </div>
    </el-header>

    <!-- 知识列表展示区 -->
    <el-main class="knowledge-list-main">
      <!-- 【修改】直接将表格数据绑定到 knowledgeList，不再需要 paginatedKnowledgeList -->
      <el-table :data="knowledgeList" border stripe v-loading="tableLoading" class="knowledge-table">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="title" label="标题/名称" show-overflow-tooltip></el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.type)">{{ getTypeName(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="100"></el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusTagName(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <!-- 【新增】编辑按钮的 Tooltip -->
            <el-tooltip content="编辑" placement="top" effect="dark">
              <el-button circle :icon="Edit" @click="editKnowledge(row)" class="action-button edit-button"></el-button>
            </el-tooltip>

            <!-- 【新增】删除按钮的 Tooltip -->
            <el-popconfirm
                title="确定要删除此知识吗？"
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="deleteKnowledge(row.id)"
                popper-class="custom-popconfirm"
            >
              <template #reference>
                <el-tooltip content="删除" placement="top" effect="dark">
                  <el-button circle :icon="Delete" class="action-button delete-button"></el-button>
                </el-tooltip>
              </template>
            </el-popconfirm>

            <!-- 【新增】更多按钮的 Tooltip -->
            <el-tooltip content="更多" placement="top" effect="dark">
              <el-button circle :icon="MoreFilled" @click="previewKnowledge(row)" class="action-button more-button"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <el-pagination
          class="pagination"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
      ></el-pagination>
    </el-main>

    <!-- ... 省略弹窗部分，这部分无需修改 ... -->
    <!-- 添加/编辑知识弹窗 -->
    <el-dialog
        v-model="addOrEditDialogVisible"
        :title="isEditing ? '编辑知识' : '添加知识'"
        width="60%"
        @close="resetForm"
    >
      <el-form :model="knowledgeForm" :rules="formRules" ref="knowledgeFormRef" label-width="100px">
        <el-form-item label="知识标题" prop="title">
          <el-input v-model="knowledgeForm.title" placeholder="请输入知识标题"></el-input>
        </el-form-item>
        <el-form-item label="知识类型" prop="type">
          <el-select v-model="knowledgeForm.type" placeholder="请选择知识类型" style="width: 100%;">
            <el-option
                v-for="item in knowledgeTypes"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="内容输入" prop="content">
          <!-- 如果有文件上传，禁用手动输入 -->
          <el-input
              v-model="knowledgeForm.content"
              type="textarea"
              :autosize="{ minRows: 5, maxRows: 15 }"
              placeholder="可以直接粘贴或输入文本内容"
              :disabled="!!knowledgeForm.fileUrl"
          ></el-input>
        </el-form-item>
        <el-form-item label="文件上传">
          <!-- 如果有手动输入内容，禁用文件上传 -->
          <!-- 如果已经有文件，也禁用文件上传 -->
          <!-- 如果 user_id 不存在，也禁用文件上传 -->
          <el-upload
              class="upload-demo"
              drag
              :action="uploadUrl"
              :on-success="handleFileUploadSuccess"
              :on-error="handleFileUploadError"
              :on-remove="handleFileRemove"
              :file-list="fileList"
              :limit="1"
              accept=".pdf,.txt,.md,.doc,.docx"
              :disabled="!!knowledgeForm.content || !!knowledgeForm.fileUrl || !currentUser?.id"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF, TXT, Markdown, DOC, DOCX 文件，单次仅支持上传一个文件。
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addOrEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitKnowledgeForm">提交</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 知识预览弹窗 -->
    <el-dialog v-model="previewDialogVisible" title="知识内容预览" width="70%">
      <div class="preview-content-wrapper">
        <pre class="preview-content">{{ previewContent }}</pre>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="previewDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { ElMessage, ElLoading } from 'element-plus';
// 【修改】导入 MoreFilled 图标，移除 View 图标
import { Search, Plus, Refresh, Edit, Delete, UploadFilled, MoreFilled } from '@element-plus/icons-vue';
import axios from 'axios';

// --- 配置后端API基础URL ---
const API_BASE_URL = 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;

// --- 响应式数据 ---
const knowledgeList = ref([]);
const searchKeyword = ref('');
const knowledgeTypeFilter = ref('');
const knowledgeStatusFilter = ref('');
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const tableLoading = ref(false);
const rebuildingIndexLoading = ref(false);

const addOrEditDialogVisible = ref(false);
const isEditing = ref(false);
const knowledgeFormRef = ref(null);
const knowledgeForm = reactive({
  id: null,
  title: '',
  type: '',
  content: '',
  fileUrl: '',
});
const fileList = ref([]);

const previewDialogVisible = ref(false);
const previewContent = ref('');

const knowledgeTypes = [
  { label: '招生政策', value: 'policy' },
  { label: '专业介绍', value: 'major' },
  { label: '校园生活', value: 'campus' },
  { label: 'FAQ', value: 'faq' },
];

const knowledgeStatuses = [
  { label: '已处理', value: 'processed' },
  { label: '待处理', value: 'pending' },
  { label: '处理失败', value: 'failed' },
];

const currentUser = ref(null);
const uploadUrl = computed(() => {
  if (currentUser.value && currentUser.value.id) {
    return `${API_BASE_URL}/knowledge/upload_file?user_id=${currentUser.value.id}`;
  }
  return '';
});

const formRules = reactive({
  title: [{ required: true, message: '请输入知识标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择知识类型', trigger: 'change' }],
  content: [
    {
      required: true,
      message: '请输入知识内容或上传文件',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (!knowledgeForm.content && !knowledgeForm.fileUrl) {
          callback(new Error('请输入知识内容或上传文件'));
        } else {
          callback();
        }
      },
    },
  ],
});


// --- 【移除】前端分页的计算属性 ---
// const filteredKnowledgeList = computed(() => { ... });
// const paginatedKnowledgeList = computed(() => { ... });
// 这两个计算属性不再需要，因为分页和筛选已由后端处理。


// --- 方法 ---

// 【修改】获取知识列表函数以支持后端分页
const fetchKnowledgeList = async () => {
  tableLoading.value = true;
  try {
    if (!currentUser.value || !currentUser.value.id) {
      ElMessage.warning('请先登录以获取用户ID，才能管理知识库。');
      tableLoading.value = false;
      return;
    }

    const params = {
      // 后端分页通常需要 pageNum 和 pageSize，或者 skip 和 limit
      // 这里我们使用 skip 和 limit 的方式
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search_keyword: searchKeyword.value,
      knowledge_type: knowledgeTypeFilter.value,
      knowledge_status: knowledgeStatusFilter.value,
      user_id: currentUser.value.id,
    };

    // 假设后端返回的数据结构是: { "data": [...], "total": 100 }
    // "data" 是当前页的条目列表
    // "total" 是符合筛选条件的总条目数
    const response = await axios.get('/knowledge', { params }); // 假设获取列表的API是 /knowledge/list

    // 使用后端返回的数据更新列表和总数
    knowledgeList.value = response.data.data;
    total.value = response.data.total;

  } catch (error) {
    ElMessage.error('获取知识列表失败！');
    console.error('Error fetching knowledge list:', error.response?.data || error);
    // 【新增】请求失败时，清空列表和总数，避免显示旧数据
    knowledgeList.value = [];
    total.value = 0;
  } finally {
    tableLoading.value = false;
  }
};

// 【新增】处理搜索和筛选变化的函数
const handleFilterChange = () => {
  // 当用户进行搜索或筛选时，重置到第一页
  currentPage.value = 1;
  fetchKnowledgeList();
};


// ... resetForm, openAddDialog, editKnowledge 等函数保持不变 ...
const resetForm = () => {
  knowledgeFormRef.value?.resetFields();
  Object.assign(knowledgeForm, {
    id: null,
    title: '',
    type: '',
    content: '',
    fileUrl: '',
  });
  fileList.value = [];
};

const openAddDialog = () => {
  isEditing.value = false;
  resetForm();
  addOrEditDialogVisible.value = true;
};

const editKnowledge = (row) => {
  isEditing.value = true;
  Object.assign(knowledgeForm, JSON.parse(JSON.stringify(row)));
  if (row.file_path) {
    const fileName = row.file_path.substring(row.file_path.lastIndexOf('/') + 1);
    fileList.value = [{ name: fileName, url: `${API_BASE_URL}/static/${row.file_path}`, status: 'success', uid: Date.now() }];
    knowledgeForm.fileUrl = row.file_path;
  } else {
    knowledgeForm.fileUrl = '';
    fileList.value = [];
  }
  addOrEditDialogVisible.value = true;
};

// 提交知识表单 (添加或编辑)
const submitKnowledgeForm = async () => {
  if (!knowledgeFormRef.value) return;
  try {
    await knowledgeFormRef.value.validate();
    tableLoading.value = true;
    if (!currentUser.value || !currentUser.value.id) {
      ElMessage.warning('用户ID缺失，无法提交操作。请重新登录。');
      tableLoading.value = false;
      return;
    }
    const dataToSend = {
      title: knowledgeForm.title,
      type: knowledgeForm.type,
      content: knowledgeForm.content,
      file_path: knowledgeForm.fileUrl,
    };
    if (isEditing.value) {
      await axios.put(`/knowledge/${knowledgeForm.id}`, dataToSend, {
        params: { user_id: currentUser.value.id },
      });
      ElMessage.success('知识更新成功！');
    } else {
      await axios.post('/knowledge', dataToSend, {
        params: { user_id: currentUser.value.id },
      });
      ElMessage.success('知识添加成功！');
    }
    addOrEditDialogVisible.value = false;
    // 【修改】提交成功后，最好是刷新当前页数据，而不是跳回第一页
    // 如果是新增操作，跳回第一页查看最新添加的项是合理的
    if (!isEditing.value) {
      currentPage.value = 1;
    }
    await fetchKnowledgeList();
  } catch (error) {
    const errorMessage = error.response?.data?.detail || '操作失败！';
    ElMessage.error(errorMessage);
  } finally {
    tableLoading.value = false;
  }
};

// 删除知识 (软删除)
const deleteKnowledge = async (id) => {
  tableLoading.value = true;
  try {
    if (!currentUser.value || !currentUser.value.id) {
      ElMessage.warning('用户ID缺失，无法执行删除操作。请重新登录。');
      tableLoading.value = false;
      return;
    }
    await axios.delete(`/knowledge/${id}`, {
      params: { user_id: currentUser.value.id },
    });
    ElMessage.success('知识删除成功！');
    // 【修改】如果删除后当前页没有数据了，应该尝试请求前一页
    if (knowledgeList.value.length === 1 && currentPage.value > 1) {
      currentPage.value--;
    }
    await fetchKnowledgeList();
  } catch (error) {
    const errorMessage = error.response?.data?.detail || '删除失败！';
    ElMessage.error(errorMessage);
  } finally {
    tableLoading.value = false;
  }
};

// ... previewKnowledge, rebuildIndex, 文件上传处理等函数保持不变 ...
const previewKnowledge = (row) => {
  previewContent.value = row.content || '无内容';
  previewDialogVisible.value = true;
};

const rebuildIndex = async () => {
  rebuildingIndexLoading.value = true;
  const loadingInstance = ElLoading.service({
    lock: true,
    text: '正在触发知识库索引重建，请稍候...',
    background: 'rgba(0, 0, 0, 0.7)',
  });
  try {
    if (!currentUser.value || !currentUser.value.id) {
      ElMessage.warning('用户ID缺失，无法执行重建索引操作。');
      loadingInstance.close();
      rebuildingIndexLoading.value = false;
      return;
    }
    await axios.post('/knowledge/rebuild_index', {}, {
      params: { user_id: currentUser.value.id },
    });
    ElMessage.success('知识库索引重建任务已成功触发！');
    setTimeout(async () => {
      await fetchKnowledgeList();
      loadingInstance.close();
      rebuildingIndexLoading.value = false;
    }, 3000);
  } catch (error) {
    loadingInstance.close();
    rebuildingIndexLoading.value = false;
    const errorMessage = error.response?.data?.detail || '重建知识库索引失败！';
    ElMessage.error(errorMessage);
  }
};

const handleFileUploadSuccess = (response, uploadFile) => {
  knowledgeForm.fileUrl = response.file_path;
  knowledgeForm.content = '';
  fileList.value = [{ name: uploadFile.name, url: `${API_BASE_URL}/static/${response.file_path}`, status: 'success', uid: uploadFile.uid }];
  ElMessage.success(`${uploadFile.name} 上传成功！`);
  knowledgeFormRef.value?.validateField('content');
};

const handleFileUploadError = (error, uploadFile) => {
  ElMessage.error(`${uploadFile.name} 上传失败！`);
  fileList.value = [];
  knowledgeForm.fileUrl = '';
  knowledgeFormRef.value?.validateField('content');
};

const handleFileRemove = (file) => {
  knowledgeForm.fileUrl = '';
  knowledgeForm.content = '';
  fileList.value = [];
  ElMessage.info(`${file.name} 已移除。`);
  knowledgeFormRef.value?.validateField('content');
};

// 分页器：每页显示数量改变
const handleSizeChange = (val) => {
  pageSize.value = val;
  currentPage.value = 1;
  fetchKnowledgeList();
};

// 分页器：当前页改变
const handlePageChange = (val) => {
  currentPage.value = val;
  fetchKnowledgeList();
};


// ... 辅助函数保持不变 ...
const getTypeTag = (type) => {
  switch (type) {
    case 'policy': return 'warning';
    case 'major': return '';
    case 'campus': return 'info';
    case 'faq': return 'success';
    default: return '';
  }
};
const getTypeName = (type) => {
  return knowledgeTypes.find(item => item.value === type)?.label || type;
};
const getStatusTagType = (status) => {
  switch (status) {
    case 'processed': return 'success';
    case 'pending': return 'info';
    case 'failed': return 'danger';
    default: return '';
  }
};
const getStatusTagName = (status) => {
  return knowledgeStatuses.find(item => item.value === status)?.label || status;
};
const formatDateTime = (isoString) => {
  if (!isoString) return '';
  return new Date(isoString).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-');
};


// 组件挂载时加载初始数据
onMounted(() => {
  const storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
  if (storedUser) {
    try {
      currentUser.value = JSON.parse(storedUser);
      console.log('KnowledgeBaseManagement: Current User ID on mount:', currentUser.value.id);
      fetchKnowledgeList(); // 获取到用户ID后再加载数据
    } catch (e) {
      console.error('KnowledgeBaseManagement: Failed to parse user data from storage:', e);
      currentUser.value = null;
      ElMessage.error('无法获取用户登录信息，请重新登录。');
    }
  } else {
    ElMessage.warning('未检测到用户登录信息，部分功能可能受限。');
  }
});
</script>

<style scoped>
/* ... 样式部分无需修改 ... */
/* 整体容器样式 */
.knowledge-base-management {
  padding: 20px;
  background-color: #f5f7fa; /* 页面背景色 */
  min-height: calc(100vh - 40px);
  transition: background-color 0.3s;
  font-size: 14px; /* 【修改】设置页面基础字体大小 */
}

/* 顶部操作栏样式 */
.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background-color: #fff;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  height: auto;
  flex-wrap: wrap;
  gap: 15px;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.header-toolbar .title {
  font-size: 26px; /* 【修改】标题字体增大 */
  font-weight: bold;
  color: #333;
  min-width: 150px;
  transition: color 0.3s;
}

.header-toolbar .controls {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.search-input { width: 280px; }
.filter-select { width: 150px; }
.add-button, .rebuild-button { min-width: 120px; }

/* 【新增】统一 Element Plus 输入框/选择器/按钮的字体大小 */
.search-input :deep(.el-input__inner),
.filter-select :deep(.el-input__inner),
.el-button {
  font-size: 15px !important;
}

/* 知识列表主内容区样式 */
.knowledge-list-main {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: background-color 0.3s, box-shadow 0.3s;
}

.knowledge-table {
  width: 100%;
  margin-bottom: 20px;
}

/* 【新增】表格头部和内容字体大小 */
.knowledge-table :deep(.el-table__header-wrapper th .cell),
.knowledge-table :deep(.el-table__body-wrapper td .cell) {
  font-size: 14px !important;
}

/* 分页器样式 */
.pagination {
  justify-content: flex-end;
  margin-top: 20px;
}

/* 【新增】分页器字体大小 */
.pagination :deep(.el-pagination__total),
.pagination :deep(.el-pagination__sizes),
.pagination :deep(.el-pagination__jump),
.pagination :deep(.el-pager li) {
  font-size: 14px !important;
}

/* 知识预览弹窗内容区样式 */
.preview-content-wrapper {
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid #eee;
  padding: 15px;
  border-radius: 4px;
  background-color: #f9f9f9;
  transition: background-color 0.3s, border-color 0.3s;
}

.preview-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', 'Andale Mono', 'Ubuntu Mono', monospace;
  font-size: 18px; /* 【修改】预览内容字体进一步增大 */
  line-height: 1.6;
  color: #333;
  transition: color 0.3s;
}

/* Element Plus Upload 组件样式调整 */
.upload-demo :deep(.el-upload-dragger) {
  padding: 20px;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s, border-color 0.3s;
}

.upload-demo .el-icon--upload { margin-bottom: 10px; }
.upload-demo .el-upload__text em {
  color: var(--el-color-primary);
  font-style: normal;
}

/* 【新增】表单标签和输入框/选择器字体大小 */
.el-form-item__label {
  font-size: 14px !important;
}
.el-form-item :deep(.el-input__inner),
.el-form-item :deep(.el-textarea__inner) {
  font-size: 14px !important;
}


/* ----------------------------------- */
/* --- [新增] 暗黑模式全局样式变量 --- */
/* ----------------------------------- */
html.dark {
  /* 定义Element Plus组件在暗黑模式下的核心颜色变量 */
  --el-bg-color: #141414;
  --el-bg-color-overlay: #1d1d1d;
  --el-border-color: #414141;
  --el-border-color-light: #353535;
  --el-border-color-lighter: #2a2a2a;
  --el-fill-color: #414141;
  --el-fill-color-light: #353535;
  --el-fill-color-lighter: #2a2a2a;
  --el-fill-color-blank: transparent;
  --el-text-color-primary: #e5eaf3;
  --el-text-color-regular: #cfd3dc;
  --el-text-color-secondary: #a3a6ad;
  --el-text-color-placeholder: #8d9095;
}

/* ----------------------------- */
/* --- [新增] 组件内暗黑模式样式 --- */
/* ----------------------------- */
html.dark .knowledge-base-management {
  background-color: #1a202c; /* 更深的页面背景 */
}

html.dark .header-toolbar,
html.dark .knowledge-list-main {
  background-color: #2d3748; /* 卡片背景色 */
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
  border: 1px solid #4a5568;
}

html.dark .header-toolbar .title {
  color: #edf2f7; /* 标题文字颜色 */
}

/* 预览弹窗样式 */
html.dark .preview-content-wrapper {
  background-color: #1a202c;
  border-color: #4a5568;
}

html.dark .preview-content {
  color: #cbd5e0;
}

/* 上传组件拖拽区域样式 */
html.dark .upload-demo :deep(.el-upload-dragger) {
  background-color: #1a202c;
  border-color: #4a5568;
}
html.dark .upload-demo :deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
}

/* ----------------------------- */
/* --- 【新增】自定义 Popconfirm 样式 --- */
/* ----------------------------- */
.custom-popconfirm {
  /* 整体弹窗大小和内边距 */
  min-width: 280px !important; /* 增加最小宽度 */
  padding: 20px !important;    /* 增加内边距 */
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important; /* 调整阴影使其更明显 */
}

/* 弹窗内容区样式 */
.custom-popconfirm .el-popconfirm__main {
  font-size: 18px !important; /* 【修改】增大文本字体 */
  margin-bottom: 15px !important; /* 增加文本与按钮之间的间距 */
  display: flex; /* 使用 flexbox 更好地对齐图标和文本 */
  align-items: center;
  color: #333; /* 确保在亮色模式下文本颜色清晰 */
}

/* 弹窗中的图标样式 */
.custom-popconfirm .el-popconfirm__main .el-icon {
  font-size: 22px !important; /* 【修改】增大图标 */
  margin-right: 8px !important;
  color: var(--el-color-warning); /* 使用 Element Plus 的警告色 */
}

/* 弹窗底部按钮区域样式 */
.custom-popconfirm .el-popconfirm__action {
  display: flex;
  justify-content: flex-end; /* 按钮靠右对齐 */
  gap: 10px; /* 按钮之间的间距 */
}

/* 弹窗中的按钮样式 */
.custom-popconfirm .el-button {
  padding: 8px 18px !important; /* 调整按钮内边距 */
  font-size: 15px !important; /* 【修改】调整按钮字体大小 */
}

/* 暗黑模式下 Popconfirm 弹窗的样式 */
html.dark .custom-popconfirm {
  background: #2d3748 !important; /* 暗黑模式背景色 */
  border: 1px solid #4a5568 !important; /* 暗黑模式边框色 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important; /* 暗黑模式阴影 */
}
html.dark .custom-popconfirm .el-popconfirm__main {
  color: #edf2f7 !important; /* 暗黑模式文本颜色 */
}
html.dark .custom-popconfirm.el-popper__arrow::before {
  background: #2d3748 !important; /* 暗黑模式箭头背景色 */
  border-color: #4a5568 !important; /* 暗黑模式箭头边框色 */
}

/* 【新增】操作列按钮样式 */
.action-button {
  width: 40px; /* 调整按钮大小 */
  height: 40px;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  border: none; /* 移除边框 */
  color: #fff !important; /* 默认图标颜色为白色，使用 !important 确保覆盖 Element Plus 默认样式 */
  font-size: 20px !important; /* 调整图标大小，使用 !important */
  margin: 0 4px; /* 按钮之间间距 */
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 50%; /* 确保是圆形 */
  padding: 0; /* 移除内边距 */
}

.action-button:hover {
  transform: translateY(-2px); /* 悬停效果 */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* 悬停阴影 */
}

.edit-button {
  background-color: #409eff; /* Element Plus primary blue */
}

.delete-button {
  background-color: #f56c6c; /* Element Plus danger red */
}

.more-button {
  background-color: #909399; /* Element Plus info grey */
}

/* 暗黑模式下的操作按钮样式 */
html.dark .action-button {
  color: #fff !important; /* 确保暗黑模式下图标也是白色 */
}

html.dark .edit-button {
  background-color: #409eff; /* 保持蓝色 */
}

html.dark .delete-button {
  background-color: #f56c6c; /* 保持红色 */
}

html.dark .more-button {
  background-color: #909399; /* 保持灰色 */
}
</style>