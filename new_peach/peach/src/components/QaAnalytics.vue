<template>
  <div class="qa-analytics-container">
    <el-row :gutter="20" class="overview-dashboard">
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="card-header">总提问数</div>
          <div class="card-value">{{ overviewData.totalQuestions }}</div>
          <el-icon class="card-icon"><ChatLineSquare /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="card-header">独立用户数</div>
          <div class="card-value">{{ overviewData.uniqueUsers }}</div>
          <el-icon class="card-icon"><User /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="card-header">未解决问题数</div>
          <div class="card-value">{{ overviewData.unresolvedQuestions }}</div>
          <el-icon class="card-icon"><Warning /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="card-header">平均会话问题数</div>
          <div class="card-value">{{ overviewData.avgQuestionsPerSession }}</div>
          <el-icon class="card-icon"><Message /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-section">
      <el-col :span="18">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header-with-date">
              <span>提问趋势图</span>
              <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  @change="handleDateRangeChange"
                  size="small"
                  value-format="YYYY-MM-DD"
              />
            </div>
          </template>
          <div ref="questionTrendChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <span>热门问题 Top 10</span>
          </template>
          <div ref="popularQuestionsChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="qa-records-section">
      <template #header>
        <div class="qa-records-header">
          <span>问答记录列表</span>
          <div class="filter-actions">
            <el-input
                v-model="searchQuery.keyword"
                placeholder="搜索问题或回答关键词"
                clearable
                style="width: 200px; margin-right: 10px;"
                @keyup.enter="fetchQaRecords"
            />
            <el-select
                v-model="searchQuery.status"
                placeholder="解决状态"
                clearable
                style="width: 120px; margin-right: 10px;"
            >
              <el-option label="已解决" value="resolved"></el-option>
              <el-option label="未解决" value="unresolved"></el-option>
              <el-option label="待处理" value="pending"></el-option>
            </el-select>
            <el-select
                v-model="searchQuery.feedback"
                placeholder="AI反馈"
                clearable
                style="width: 120px; margin-right: 10px;"
            >
              <el-option label="满意" value="satisfied"></el-option>
              <el-option label="满意 (Like)" value="like"></el-option> <!-- 新增：如果后端可能返回 'like' -->
              <el-option label="不满意" value="dissatisfied"></el-option>
              <el-option label="不满意 (Dislike)" value="dislike"></el-option>
            </el-select>
            <el-date-picker
                v-model="searchQuery.recordDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="记录开始日期"
                end-placeholder="记录结束日期"
                value-format="YYYY-MM-DD"
                style="width: 260px; margin-right: 10px;"
            />
            <el-button type="primary" :icon="Search" @click="fetchQaRecords">查询</el-button>
            <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
            <el-button :icon="Download" @click="exportData">导出数据</el-button>
          </div>
        </div>
      </template>

      <el-table :data="qaRecords" v-loading="loadingTable" style="width: 100%" border>
        <el-table-column type="index" label="序号" width="60" align="center" :index="indexMethod"></el-table-column>
        <el-table-column prop="userId" label="用户ID" width="90" align="center"></el-table-column>
        <!-- 进一步缩短用户问题摘要的最小宽度 -->
        <el-table-column prop="userQuestionSummary" label="用户问题摘要" min-width="100" show-overflow-tooltip></el-table-column>
        <!-- 进一步缩短AI回答摘要的最小宽度 -->
        <el-table-column prop="aiAnswerSummary" label="AI回答摘要" min-width="100" show-overflow-tooltip></el-table-column>
        <!-- 提问时间宽度保持不变，因为它已经是日期时间格式的最小合理宽度 -->
        <el-table-column prop="timestamp" label="提问时间" width="150" sortable></el-table-column>
        <!-- 解决状态宽度保持不变 -->
        <el-table-column prop="status" label="解决状态" width="80" align="center">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- AI反馈宽度保持不变 -->
        <el-table-column prop="feedback" label="AI反馈" width="80" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.feedback" :type="getFeedbackTagType(scope.row.feedback)">
              {{ getFeedbackText(scope.row.feedback) }}
            </el-tag>
            <span v-else>无</span>
          </template>
        </el-table-column>
        <!-- 操作列宽度保持240px，确保内容完整显示 -->
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="scope">
            <!-- 使用 Flexbox 容器确保垂直对齐，并设置更小的 gap -->
            <div class="action-buttons-wrapper">
              <el-button type="primary" size="small" :icon="View" text @click="viewDetail(scope.row)">查看详情</el-button>
              <el-dropdown trigger="click" @command="(command) => updateQaStatus(scope.row, command)">
                <el-button type="primary" size="small" :icon="Edit" text>
                  标记状态<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="resolved">已解决</el-dropdown-item>
                    <el-dropdown-item command="unresolved">未解决</el-dropdown-item>
                    <el-dropdown-item command="pending">待处理</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-popconfirm
                  title="确定删除此记录吗？"
                  confirm-button-text="是"
                  cancel-button-text="否"
                  @confirm="deleteRecord(scope.row.id)"
              >
                <template #reference>
                  <el-button type="danger" size="small" :icon="Delete" text>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :small="false"
          :disabled="loadingTable"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          class="pagination-container"
      />
    </el-card>

    <el-dialog
        v-model="dialogVisible"
        :title="`问答详情 - 用户ID: ${currentQaDetail?.userId}`"
        width="60%"
        destroy-on-close
    >
      <div v-if="currentQaDetail" class="qa-detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="会话ID">{{ currentQaDetail.sessionId }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ currentQaDetail.userId }}</el-descriptions-item>
          <el-descriptions-item label="提问时间">{{ currentQaDetail.timestamp }}</el-descriptions-item>
          <el-descriptions-item label="解决状态">
            <el-tag :type="getStatusTagType(currentQaDetail.status)">
              {{ getStatusText(currentQaDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户问题" :span="2">
            <div class="detail-text">{{ currentQaDetail.userQuestion }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="AI回答" :span="2">
            <div class="detail-text">{{ currentQaDetail.aiAnswer || '无回答' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="AI引用知识库上下文" :span="2">
            <div class="detail-text context-area">
              <p v-for="(context, index) in currentQaDetail.knowledgeBaseContext" :key="index">
                <strong>片段 {{ index + 1 }}:</strong> {{ context }}
              </p>
              <span v-if="!currentQaDetail.knowledgeBaseContext || currentQaDetail.knowledgeBaseContext.length === 0">
                AI回答未引用特定知识库片段。
              </span>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <div class="admin-notes-section">
          <h3>管理员备注</h3>
          <el-input
              v-model="currentQaDetail.adminNotes"
              type="textarea"
              :rows="4"
              placeholder="在此处添加对该问答记录的备注或分析..."
          ></el-input>
          <div class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" :icon="Check" @click="saveAdminNotes">保存备注</el-button>
            <el-dropdown trigger="click" @command="(command) => updateQaStatus(currentQaDetail, command, true)">
              <el-button type="warning" :icon="Edit" text>
                修改状态<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="resolved">已解决</el-dropdown-item>
                  <el-dropdown-item command="unresolved">未解决</el-dropdown-item>
                  <el-dropdown-item command="pending">待处理</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import {
  Search, Refresh, Download, ChatLineSquare, User, Warning, Message, ArrowDown,
  View, Edit, Delete, Check
} from '@element-plus/icons-vue';
import axios from 'axios';

// --- 配置后端API基础URL ---
const BASE_API_URL = 'http://localhost:8000'; // 确保与您的FastAPI服务地址匹配

// --- 响应式数据 ---
const overviewData = reactive({
  totalQuestions: 0,
  uniqueUsers: 0,
  unresolvedQuestions: 0,
  avgQuestionsPerSession: 0,
});

const dateRange = ref([]);
const loadingTable = ref(false);
const loadingCharts = ref(false);

const qaRecords = ref([]);
const searchQuery = reactive({
  keyword: '',
  status: '',
  feedback: '',
  recordDateRange: [],
});

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
});

const dialogVisible = ref(false);
const currentQaDetail = ref(null);

// ECharts 实例引用
const questionTrendChartRef = ref(null);
const popularQuestionsChartRef = ref(null);
let questionTrendChartInstance = null;
let popularQuestionsChartInstance = null;

const currentUserId = ref(null);

// [新增] 响应式引用，用于跟踪当前是否为暗黑模式
const isDarkMode = ref(document.documentElement.classList.contains('dark'));
let themeObserver = null;


// --- 方法 ---

// 生成序号的方法
const indexMethod = (index) => {
  return (pagination.currentPage - 1) * pagination.pageSize + index + 1;
};

// 获取当前默认时间范围 (过去7天)
const getDefaultDateRange = () => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 6); // 过去7天
  return [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ];
};

const fetchOverviewData = async () => {
  if (!currentUserId.value) {
    ElMessage.error('用户ID未获取，无法加载概览数据。');
    return;
  }
  loadingCharts.value = true;
  const [startDate, endDate] = dateRange.value.length === 2 ? dateRange.value : getDefaultDateRange();
  try {
    const response = await axios.get(`${BASE_API_URL}/qa_analytics/overview`, {
      params: { start_date: startDate, end_date: endDate, user_id: currentUserId.value },
    });
    Object.assign(overviewData, response.data);
  } catch (error) {
    ElMessage.error('获取概览数据失败');
    console.error('获取概览数据失败:', error);
  } finally {
    loadingCharts.value = false;
  }
};

const fetchChartData = async () => {
  if (!currentUserId.value) {
    ElMessage.error('用户ID未获取，无法加载图表数据。');
    return;
  }
  loadingCharts.value = true;
  const [startDate, endDate] = dateRange.value.length === 2 ? dateRange.value : getDefaultDateRange();
  try {
    const response = await axios.get(`${BASE_API_URL}/qa_analytics/charts`, {
      params: { start_date: startDate, end_date: endDate, user_id: currentUserId.value },
    });
    renderQuestionTrendChart(response.data.questionTrend);
    renderPopularQuestionsChart(response.data.popularQuestions);
  } catch (error)
  {
    ElMessage.error('获取图表数据失败');
    console.error('获取图表数据失败:', error);
  } finally {
    loadingCharts.value = false;
  }
};

const fetchQaRecords = async () => {
  if (!currentUserId.value) {
    ElMessage.error('用户ID未获取，无法加载问答记录。');
    return;
  }
  loadingTable.value = true;
  try {
    const params = {
      skip: (pagination.currentPage - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      keyword: searchQuery.keyword || undefined,
      status: searchQuery.status || undefined,
      feedback: searchQuery.feedback || undefined, // 后端需要能够处理 'satisfied', 'like', 'dissatisfied', 'dislike'
      record_start_date: searchQuery.recordDateRange?.[0] || undefined,
      record_end_date: searchQuery.recordDateRange?.[1] || undefined,
      user_id: currentUserId.value,
    };
    const response = await axios.get(`${BASE_API_URL}/qa_analytics/records`, { params });
    qaRecords.value = response.data.records;
    pagination.total = response.data.total;
  } catch (error) {
    ElMessage.error('获取问答记录失败');
    console.error('获取问答记录失败:', error);
  } finally {
    loadingTable.value = false;
  }
};

const handleDateRangeChange = () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    dateRange.value = getDefaultDateRange();
  }
  fetchOverviewData();
  fetchChartData();
};

const resetSearch = () => {
  searchQuery.keyword = '';
  searchQuery.status = '';
  searchQuery.feedback = '';
  searchQuery.recordDateRange = [];
  pagination.currentPage = 1;
  fetchQaRecords();
};

const exportData = () => {
  ElMessage.info('导出数据功能待实现...');
};

const viewDetail = async (record) => {
  if (!currentUserId.value) {
    ElMessage.error('用户ID未获取，无法查看详情。');
    return;
  }
  try {
    const response = await axios.get(`${BASE_API_URL}/qa_analytics/records/${record.id}`, {
      params: { user_id: currentUserId.value },
    });
    currentQaDetail.value = response.data;
    dialogVisible.value = true;
  } catch (error) {
    ElMessage.error('获取问答详情失败');
    console.error('获取问答详情失败:', error);
  }
};

const updateQaStatus = async (record, newStatus, fromDialog = false) => {
  if (!currentUserId.value) {
    ElMessage.error('用户ID未获取，无法更新状态。');
    return;
  }
  const oldStatus = record.status;

  if (!fromDialog) {
    record.status = newStatus;
  } else if (currentQaDetail.value) {
    currentQaDetail.value.status = newStatus;
  }

  try {
    const payload = {
      status: newStatus,
      adminNotes: fromDialog ? currentQaDetail.value.adminNotes : record.adminNotes,
      feedback: fromDialog ? currentQaDetail.value.feedback : record.feedback,
    };
    await axios.put(`${BASE_API_URL}/qa_analytics/records/${record.id}`, payload, {
      params: { user_id: currentUserId.value },
    });
    ElMessage.success(`问答记录 ${record.id} 状态已更新为 ${getStatusText(newStatus)}`);
    fetchOverviewData();
    fetchQaRecords();
    if (fromDialog) {
      dialogVisible.value = false;
    }
  } catch (error) {
    ElMessage.error('更新状态失败');
    console.error('更新状态失败:', error);
    if (!fromDialog) {
      record.status = oldStatus;
    } else if (currentQaDetail.value) {
      currentQaDetail.value.status = oldStatus;
    }
  }
};

const deleteRecord = async (recordId) => {
  if (!currentUserId.value) {
    ElMessage.error('用户ID未获取，无法删除记录。');
    return;
  }
  try {
    await axios.delete(`${BASE_API_URL}/qa_analytics/records/${recordId}`, {
      params: { user_id: currentUserId.value },
    });
    ElMessage.success(`问答记录 ${recordId} 已删除`);
    fetchOverviewData();
    fetchQaRecords();
  } catch (error) {
    ElMessage.error('删除记录失败');
    console.error('删除记录失败:', error);
  }
};

const saveAdminNotes = async () => {
  if (!currentQaDetail.value || !currentUserId.value) {
    ElMessage.error('用户ID或问答详情未获取，无法保存备注。');
    return;
  }
  try {
    const payload = {
      adminNotes: currentQaDetail.value.adminNotes,
      status: currentQaDetail.value.status,
      feedback: currentQaDetail.value.feedback,
    };
    await axios.put(`${BASE_API_URL}/qa_analytics/records/${currentQaDetail.value.id}`, payload, {
      params: { user_id: currentUserId.value },
    });
    ElMessage.success('管理员备注已保存');
    dialogVisible.value = false;
    fetchQaRecords();
  } catch (error) {
    ElMessage.error('保存备注失败');
    console.error('保存备注失败:', error);
  }
};

const handleSizeChange = (val) => {
  pagination.pageSize = val;
  fetchQaRecords();
};

const handleCurrentChange = (val) => {
  pagination.currentPage = val;
  fetchQaRecords();
};


// --- ECharts 相关 ---
const initCharts = () => {
  // [修改] 让 ECharts 实例根据当前主题动态初始化
  const theme = isDarkMode.value ? 'dark' : undefined;

  // 销毁旧实例，防止内存泄漏
  if (questionTrendChartInstance) {
    questionTrendChartInstance.dispose();
  }
  if (popularQuestionsChartInstance) {
    popularQuestionsChartInstance.dispose();
  }

  if (questionTrendChartRef.value) {
    questionTrendChartInstance = echarts.init(questionTrendChartRef.value, theme);
  }
  if (popularQuestionsChartRef.value) {
    popularQuestionsChartInstance = echarts.init(popularQuestionsChartRef.value, theme);
  }
};

const renderQuestionTrendChart = (data) => {
  if (!questionTrendChartInstance) return;

  // [修改] 为亮色和暗色模式提供不同的颜色配置
  const lightColors = {
    line: '#409EFF', // Element Plus 主色
    area: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
      { offset: 1, color: 'rgba(64, 158, 255, 0.0)' }
    ])
  };

  const darkColors = {
    line: '#58A0FD',
    area: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: 'rgba(88, 160, 253, 0.5)' },
      { offset: 1, color: 'rgba(88, 160, 253, 0.0)' }
    ])
  };

  const currentColors = isDarkMode.value ? darkColors : lightColors;

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.dates, axisLabel: { rotate: 45, interval: Math.ceil(data.dates.length / 7) } },
    yAxis: { type: 'value', name: '提问数量' },
    series: [{
      name: '提问数量',
      type: 'line',
      smooth: true,
      data: data.data,
      itemStyle: { color: currentColors.line },
      areaStyle: { color: currentColors.area }
    }]
  };
  questionTrendChartInstance.setOption(option);
};

const renderPopularQuestionsChart = (data) => {
  if (!popularQuestionsChartInstance) return;

  // [修改] 为亮色和暗色模式提供不同的颜色配置
  const lightColors = {
    bar: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
      { offset: 0, color: '#A0CFFF' },
      { offset: 1, color: '#409EFF' }
    ])
  };

  const darkColors = {
    bar: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
      { offset: 0, color: '#2989FF' },
      { offset: 1, color: '#58A0FD' }
    ])
  };

  const currentColors = isDarkMode.value ? darkColors : lightColors;

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '提问次数' },
    yAxis: { type: 'category', data: data.names.reverse(), axisLabel: { formatter: (value) => value.length > 15 ? value.substring(0, 12) + '...' : value } },
    series: [{
      name: '提问次数',
      type: 'bar',
      data: data.values.reverse(),
      itemStyle: { color: currentColors.bar }
    }]
  };
  popularQuestionsChartInstance.setOption(option);
};

// --- 工具函数 ---
const getStatusTagType = (status) => {
  switch (status) {
    case 'resolved': return 'success';
    case 'unresolved': return 'danger';
    case 'pending': return 'warning';
    default: return 'info';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'resolved': return '已解决';
    case 'unresolved': return '未解决';
    case 'pending': return '待处理';
    default: return '未知';
  }
};

const getFeedbackTagType = (feedback) => {
  switch (feedback) {
    case 'satisfied':
    case 'like': // <--- 修改点：添加 'like'
      return 'success';
    case 'dissatisfied':
    case 'dislike':
      return 'danger';
    default: return 'info';
  }
};

const getFeedbackText = (feedback) => {
  switch (feedback) {
    case 'satisfied':
    case 'like': // <--- 修改点：添加 'like'
      return '满意';
    case 'dissatisfied':
    case 'dislike':
      return '不满意';
    default: return '无反馈';
  }
};

// --- 生命周期钩子 ---
onMounted(() => {
  // [新增] 使用 MutationObserver 监听 <html> 元素 class 的变化来检测主题切换
  themeObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'class') {
        isDarkMode.value = document.documentElement.classList.contains('dark');
      }
    });
  });
  themeObserver.observe(document.documentElement, { attributes: true });

  const storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
  if (storedUser) {
    try {
      const user = JSON.parse(storedUser);
      currentUserId.value = user.id;
    } catch (e) {
      console.error('QaAnalytics.vue: 解析用户数据失败:', e);
      currentUserId.value = null;
      ElMessage.error('无法获取当前用户ID，部分功能可能受限。');
    }
  } else {
    ElMessage.warning('未找到登录用户数据，请确保已登录。');
  }

  dateRange.value = getDefaultDateRange();

  // 使用 nextTick 确保 DOM 元素已经准备好
  nextTick(() => {
    initCharts();
    if (currentUserId.value) {
      fetchOverviewData();
      fetchChartData();
      fetchQaRecords();
    }
    // 添加窗口大小变化的监听
    window.addEventListener('resize', handleResize);
  });
});

onBeforeUnmount(() => {
  // 销毁 ECharts 实例
  questionTrendChartInstance?.dispose();
  popularQuestionsChartInstance?.dispose();
  // [新增] 移除监听器，防止内存泄漏
  window.removeEventListener('resize', handleResize);
  if (themeObserver) {
    themeObserver.disconnect();
  }
});

// [新增] 监听 isDarkMode 变化，并重新渲染图表
watch(isDarkMode, async () => {
  // 重新初始化图表以应用新主题
  initCharts();
  // 重新获取数据并渲染，确保颜色等配置生效
  await nextTick(); // 等待DOM更新
  fetchChartData();
});

// [新增] 统一的 resize handler
const handleResize = () => {
  questionTrendChartInstance?.resize();
  popularQuestionsChartInstance?.resize();
}

</script>

<style lang="scss" scoped>
// 全面更新样式以适应亮/暗双主题
.qa-analytics-container {
  padding: 20px;
  // 使用Element Plus暗黑主题的页面背景色变量，可自适应主题
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);

  .el-row {
    margin-bottom: 20px;
  }

  .metric-card {
    // Element Plus的el-card在暗黑模式下会自动应用背景色
    text-align: center;
    position: relative;
    overflow: hidden;
    border: 1px solid var(--el-border-color-lighter); // 添加细微边框

    .card-header {
      font-size: 14px;
      // 使用次要文字颜色变量
      color: var(--el-text-color-secondary);
      margin-bottom: 10px;
    }
    .card-value {
      font-size: 28px;
      font-weight: bold;
      // 使用主要文字颜色变量
      color: var(--el-text-color-primary);
    }
    .card-icon {
      position: absolute;
      right: -10px;
      bottom: -10px;
      font-size: 60px;
      // [BUG修复] 使用CSS变量替换硬编码的白色，使其在亮色模式下也可见
      color: var(--el-border-color-extra-light);
    }
  }

  .card-header-with-date {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: bold;
    color: var(--el-text-color-primary);
  }

  .chart-section {
    .el-card {
      height: 380px;
      border: 1px solid var(--el-border-color-lighter);

      // 使用::v-deep或:deep()来穿透Scoped CSS
      :deep(.el-card__header) {
        padding: 15px 20px;
      }
      :deep(.el-card__body) {
        padding: 10px 20px 20px;
      }
    }
  }

  .qa-records-section {
    margin-top: 20px;
    border: 1px solid var(--el-border-color-lighter);
    .qa-records-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 16px;
      font-weight: bold;
      color: var(--el-text-color-primary);
      .filter-actions {
        display: flex;
        align-items: center;
      }
    }

    .el-table {
      margin-top: 20px;
      // el-table本身会使用Element Plus的CSS变量来自适应主题，无需额外设置背景

      // 调整：操作列按钮的垂直对齐样式，并设置更小的 gap
      .action-buttons-wrapper {
        display: flex;
        align-items: center; // 垂直居中对齐所有子元素
        justify-content: center; // 水平居中对齐整个按钮组 (因为列本身是居中对齐的)
        gap: 0px; // 进一步减小间距到0
      }
    }

    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .qa-detail-content {
    .el-descriptions {
      margin-bottom: 20px;
    }
    .detail-text {
      padding: 5px 0;
      line-height: 1.6;
      word-break: break-word;
      white-space: pre-wrap;
    }
    .context-area {
      // [BUG修复] 使用CSS变量替换硬编码的白色背景，使其在亮/暗模式下都有合适的背景色
      background-color: var(--el-fill-color);
      border-left: 3px solid var(--el-color-primary);
      padding: 10px;
      margin-top: 5px;
      border-radius: 4px;
      p {
        margin: 5px 0;
        font-size: 13px;
        color: var(--el-text-color-regular);
      }
      strong {
        color: var(--el-text-color-primary);
      }
    }

    .admin-notes-section {
      margin-top: 20px;
      h3 {
        margin-bottom: 10px;
        font-size: 16px;
        color: var(--el-text-color-primary);
      }
      .dialog-footer {
        margin-top: 20px;
        text-align: right;
        .el-button {
          margin-left: 10px;
        }
      }
    }
  }
}
</style>