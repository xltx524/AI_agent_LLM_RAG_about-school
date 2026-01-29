<!-- src/components/Dashboard.vue -->
<template>
  <div class="dashboard-container">
    <!-- 1. 顶部欢迎与快捷操作区 -->
    <div class="welcome-card" :class="{ 'dark-mode': isDarkMode }">
      <div class="welcome-text">
        <h2>欢迎回来, {{ user.name }}!</h2>
        <p>祝您今天工作愉快。系统当前状态良好。</p>
      </div>
      <div class="quick-actions">
        <el-button type="primary" :icon="User" @click="goTo('/Index/Main')">用户管理</el-button>
        <el-button :icon="Bell">发布通知</el-button>
      </div>
    </div>

    <!-- 2. 数据统计卡片区 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
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

    <!-- 3. 两栏布局：快捷入口与系统公告 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧：快捷入口 -->
      <el-col :span="12">
        <el-card shadow="hover" class="quick-links-card">
          <template #header>
            <div class="card-header">
              <span>快捷功能入口</span>
            </div>
          </template>
          <div class="quick-links-grid">
            <div class="link-item" v-for="link in quickLinks" :key="link.title" @click="goTo(link.path)">
              <el-icon class="link-icon" :style="{ color: link.color }"><component :is="link.icon" /></el-icon>
              <span>{{ link.title }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <!-- 右侧：系统公告 -->
      <el-col :span="12">
        <el-card shadow="hover" class="announcements-card">
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
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { User, Bell, ChatDotRound, DocumentAdd, TrendCharts, DataAnalysis, Setting, Collection, Position, MoreFilled, Check } from '@element-plus/icons-vue';
import axios from 'axios'; // 引入 axios

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
  fetchDashboardStats(); // 在组件挂载后立即获取仪表盘数据
});

// --- 数据统计卡片数据 (添加 key 属性用于与后端数据匹配) ---
const stats = ref([
  { title: '今日咨询量', value: '加载中...', icon: ChatDotRound, color: '#409EFF', key: 'todayConsultations' },
  { title: '待处理申请', value: '加载中...', icon: DocumentAdd, color: '#67C23A', key: 'pendingApplications' },
  { title: '本周访问量', value: '加载中...', icon: TrendCharts, color: '#E6A23C', key: 'weeklyVisits' },
  { title: '总用户数', value: '加载中...', icon: User, color: '#F56C6C', key: 'totalUsers' },
]);

// --- 快捷入口数据 ---
const quickLinks = ref([
  { title: '用户管理', icon: User, path: '/Index/Main', color: '#409EFF' },
  { title: '专业管理', icon: Collection, path: '', color: '#67C23A' },
  { title: '招生计划', icon: DataAnalysis, path: '', color: '#E6A23C' },
  { title: '发布文章', icon: Position, path: '', color: '#F56C6C' },
  { title: '系统设置', icon: Setting, path: '', color: '#909399' },
  { title: '更多功能', icon: MoreFilled, path: '', color: '#303133' },
]);

// --- 系统公告数据 ---
const activities = ref([
  { content: '2025年夏季招生简章已更新', timestamp: '2025-07-10', type: 'primary', icon: Check },
  { content: '服务器将于今晚23:00进行维护', timestamp: '2025-07-09', type: 'warning' },
  { content: '新增 "人工智能" 专业介绍页面', timestamp: '2025-07-08' },
]);

// --- 方法 ---
const goTo = (path) => {
  if (path) {
    router.push(path);
  }
};

// --- [修改] 获取仪表盘统计数据的方法 ---
const fetchDashboardStats = async () => {
  console.log('开始请求仪表盘数据...');
  try {
    // *** 关键修改：将 '/api/dashboard/stats' 修改为 '/dashboard/stats' ***
    const response = await axios.get('/dashboard/stats');
    console.log('后端响应:', response); // 打印整个响应对象
    console.log('响应状态码:', response.data.code); // 打印响应的code

    if (response.data.code === 200) {
      const backendData = response.data.data;
      console.log('后端返回的实际数据:', backendData); // 打印后端返回的data对象

      stats.value.forEach(stat => {
        if (backendData[stat.key] !== undefined) {
          // 将数字格式化为带有千位分隔符的字符串
          stat.value = backendData[stat.key].toLocaleString();
          console.log(`更新统计项: ${stat.title}, key: ${stat.key}, 新值: ${stat.value}`);
        } else {
          console.warn(`后端数据中未找到键: ${stat.key} (对应标题: ${stat.title})`);
        }
      });
    } else {
      console.error('获取仪表盘数据失败:', response.data.msg || '未知错误');
      // 可以在这里显示一个用户友好的错误提示
    }
  } catch (error) {
    console.error('请求仪表盘数据时发生错误:', error);
    // 可以在这里显示网络错误提示
  }
};
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px); /* 减去Header的高度 */
}

/* 欢迎卡片 */
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

/* 数据统计卡片 */
.stats-cards {
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

/* 主内容区 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

/* 快捷入口 */
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

/* 公告 */
.announcements-card .el-timeline {
  padding-left: 5px;
}
</style>