<template>
  <div class="user-dashboard-container">
    <!-- 1. 顶部欢迎与个人快捷操作区 -->
    <div class="welcome-card" :class="{ 'dark-mode': isDarkMode }">
      <div class="welcome-text">
        <h2>欢迎回来, {{ user.name }}!</h2>
        <p>您可以在这里查看您的申请状态和最新通知。</p>
      </div>
      <div class="quick-actions">
        <el-button type="primary" :icon="Document" @click="goTo('/user/my-applications')">我的申请</el-button>
        <el-button :icon="Plus" @click="goTo('/user/submit-application')">提交新申请</el-button>
      </div>
    </div>

    <!-- 2. 我的数据统计卡片区 -->
    <el-row :gutter="20" class="user-stats-cards">
      <el-col :span="6" v-for="stat in userStats" :key="stat.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" :style="{ backgroundColor: stat.color }">
              <component :is="stat.icon" />
            </el-icon>
            <div class="stat-details">
              <span class="stat-title">{{ stat.title }}</span>
              <span class="stat-value">{{ stat.value }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 3. 两栏布局：快捷入口与系统公告/我的最新申请 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧：快捷功能入口 -->
      <el-col :span="12">
        <el-card shadow="hover" class="quick-links-card">
          <template #header>
            <div class="card-header">
              <span>快捷功能入口</span>
            </div>
          </template>
          <div class="quick-links-grid">
            <div class="link-item" v-for="link in userQuickLinks" :key="link.title" @click="goTo(link.path)">
              <el-icon class="link-icon" :style="{ color: link.color }"><component :is="link.icon" /></el-icon>
              <span>{{ link.title }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <!-- 右侧：系统公告 或 我的最新申请 -->
      <el-col :span="12">
        <el-card shadow="hover" class="latest-application-card" v-if="latestApplication.status">
          <template #header>
            <div class="card-header">
              <span>我的最新申请</span>
              <el-button type="primary" link @click="goTo('/user/my-applications')">查看详情</el-button>
            </div>
          </template>
          <div class="application-details">
            <p><strong>申请项目:</strong> {{ latestApplication.project }}</p>
            <p><strong>申请日期:</strong> {{ latestApplication.date }}</p>
            <p><strong>当前状态:</strong>
              <el-tag :type="latestApplication.tagType">{{ latestApplication.status }}</el-tag>
            </p>
            <el-progress :percentage="latestApplication.progress" :status="latestApplication.progressStatus" striped striped-flow :duration="10" />
            <el-timeline style="margin-top: 20px;">
              <el-timeline-item
                  v-for="(activity, index) in latestApplication.timeline"
                  :key="index"
                  :icon="activity.icon"
                  :type="activity.type"
                  :timestamp="activity.timestamp"
              >
                {{ activity.content }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>

        <el-card shadow="hover" class="announcements-card" v-else>
          <template #header>
            <div class="card-header">
              <span>系统公告</span>
              <el-button type="primary" link>查看更多</el-button>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
                v-for="(activity, index) in activities"
                :key="index"
                :icon="activity.icon"
                :type="activity.type"
                :timestamp="activity.timestamp"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  User, Bell, ChatLineRound, Document, Plus, Check, Star, Tickets, School, Service,
  MoreFilled, Clock, CircleCheck, CircleClose, Loading,
  Setting // <-- 确保这里有 Setting
} from '@element-plus/icons-vue';
import axios from 'axios';

const router = useRouter();

// --- 用户信息 ---
const user = ref({ name: '访客' });
const loadUserData = () => {
  let storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
  if (storedUser) {
    user.value = JSON.parse(storedUser);
  }
};

// --- 暗色模式检测 ---
const isDarkMode = ref(document.documentElement.classList.contains('dark'));
onMounted(() => {
  const observer = new MutationObserver(() => {
    isDarkMode.value = document.documentElement.classList.contains('dark');
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  loadUserData();
  fetchUserDashboardData();
});

// --- 我的数据统计卡片数据 (模拟数据) ---
const userStats = ref([
  { title: '我的咨询数量', value: '0', icon: ChatLineRound, color: '#409EFF', key: 'myConsultations' },
  { title: '待处理申请', value: '0', icon: Document, color: '#E6A23C', key: 'myPendingApplications' },
  { title: '已通过申请', value: '0', icon: Check, color: '#67C23A', key: 'myApprovedApplications' },
  { title: '我的收藏', value: '0', icon: Star, color: '#F56C6C', key: 'myFavorites' },
]);

// --- 快捷功能入口 (用户版) ---
const userQuickLinks = ref([
  { title: '提交新申请', icon: Plus, path: '/user/submit-application', color: '#409EFF' },
  { title: '我的申请', icon: Tickets, path: '/user/my-applications', color: '#67C23A' },
  { title: '浏览专业', icon: School, path: '/user/browse-majors', color: '#E6A23C' },
  { title: '联系客服', icon: Service, path: '/user/contact-support', color: '#F56C6C' },
  { title: '个人设置', icon: Setting, path: '/user/settings', color: '#909399' },
  { title: '更多功能', icon: MoreFilled, path: '', color: '#303133' },
]);

// --- 系统公告数据 (可与管理员共享，或从后端获取用户特定公告) ---
const activities = ref([
  { content: '2025年夏季招生简章已发布，请查阅！', timestamp: '2025-07-10', type: 'primary', icon: Check },
  { content: '系统将于今晚23:00进行性能优化，可能出现短暂卡顿。', timestamp: '2025-07-09', type: 'warning' },
  { content: '“人工智能”专业新增就业指导课程，欢迎报名。', timestamp: '2025-07-08' },
  { content: '恭喜您完成新生入学登记！', timestamp: '2025-07-07', type: 'success' },
]);

// --- 我的最新申请数据 (模拟数据) ---
const latestApplication = ref({
  project: '2025年秋季计算机科学专业申请',
  date: '2025-07-01',
  status: '审核中',
  tagType: 'warning',
  progress: 60,
  progressStatus: '',
  timeline: [
    { content: '申请已提交', timestamp: '2025-07-01', type: 'success', icon: CircleCheck },
    { content: '资料初审中', timestamp: '2025-07-03', type: 'primary', icon: Loading },
    { content: '等待面试通知', timestamp: '2025-07-05', type: 'info', icon: Clock },
  ]
});

// --- 方法 ---
const goTo = (path) => {
  if (path) {
    router.push(path);
  }
};

// --- 获取用户仪表盘统计数据的方法 (模拟后端数据) ---
const fetchUserDashboardData = async () => {
  console.log('开始请求用户仪表盘数据...');
  try {
    await new Promise(resolve => setTimeout(resolve, 500));

    const mockBackendData = {
      code: 200,
      msg: "获取成功",
      data: {
        myConsultations: 15,
        myPendingApplications: 3,
        myApprovedApplications: 8,
        myFavorites: 5,
      }
    };

    if (mockBackendData.code === 200) {
      const backendData = mockBackendData.data;
      console.log('模拟后端返回的实际数据:', backendData);

      userStats.value.forEach(stat => {
        if (backendData[stat.key] !== undefined) {
          stat.value = backendData[stat.key].toLocaleString();
        }
      });
    } else {
      console.error('获取用户仪表盘数据失败:', mockBackendData.msg || '未知错误');
    }
  } catch (error) {
    console.error('请求用户仪表盘数据时发生错误:', error);
  }
};
</script>

<style scoped>
.user-dashboard-container {
  padding: 20px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}

.welcome-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px;
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  border-radius: 12px;
  color: #fff;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.welcome-card.dark-mode {
  background: linear-gradient(135deg, #1d2b3a 0%, #182848 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
.welcome-text h2 {
  margin: 0 0 5px;
  font-size: 24px;
  font-weight: 500;
}
.welcome-text p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.user-stats-cards {
  margin-bottom: 20px;
}
.stat-card .el-card__body {
  padding: 15px !important;
}
.stat-content {
  display: flex;
  align-items: center;
}
.stat-icon {
  font-size: 24px;
  padding: 12px;
  color: #fff;
  border-radius: 8px;
  margin-right: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-details {
  display: flex;
  flex-direction: column;
}
.stat-title {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-bottom: 5px;
}
.stat-value {
  color: var(--el-text-color-primary);
  font-size: 22px;
  font-weight: bold;
}

.main-content {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.quick-links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 20px;
}
.link-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 15px 0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: var(--el-bg-color-page);
}
.link-item:hover {
  transform: translateY(-5px);
  box-shadow: var(--el-box-shadow-light);
  background-color: var(--el-color-primary-light-9);
}
html.dark .link-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}
.link-icon {
  font-size: 28px;
  margin-bottom: 10px;
}

.latest-application-card .el-card__body {
  padding: 20px;
}
.application-details p {
  margin: 8px 0;
  font-size: 15px;
  color: var(--el-text-color-regular);
}
.application-details strong {
  color: var(--el-text-color-primary);
}
.el-tag {
  margin-left: 10px;
}
.el-progress {
  margin-top: 15px;
}

.announcements-card .el-timeline {
  padding-left: 5px;
}
</style>