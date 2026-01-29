<!-- Aside.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Monitor,
  HomeFilled,
  Setting,
  User,
  ChatDotSquare,    // 智能咨询 / 智能体对话
  QuestionFilled,   // 常见问题
  Collection,       // 知识库管理
  TrendCharts,      // 问答记录与分析
  Cpu,              // 模型配置
  Tickets,          // 我的咨询记录
  Document, Plus, Check, Star, School, Service, MoreFilled,
} from '@element-plus/icons-vue'

const props = defineProps({
  isCollapse: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const router = useRouter()

const currentUserRole = ref(null);

onMounted(() => {
  const storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
  if (storedUser) {
    try {
      const user = JSON.parse(storedUser);
      currentUserRole.value = user.role;
      console.log('Aside.vue: 当前用户角色为:', currentUserRole.value);
    } catch (e) {
      console.error('Aside.vue: 解析用户数据失败:', e);
      currentUserRole.value = null;
    }
  }
});

const activeMenuIndex = computed(() => {
  const currentPath = route.path;

  // 调整激活逻辑以匹配新的菜单项路径
  if (currentPath.startsWith('/Index/Home')) { // 个人中心
    return '/Index/Home'; // 确保完整路径匹配
  }
  if (currentPath === '/Index' || currentPath === '/Index/') { // 管理员仪表盘
    return '/Index';
  }
  if (currentPath === '/Index/UserDashboard') { // 用户首页
    return '/Index/UserDashboard';
  }
  if (currentPath === '/Index/Main') { // 用户管理
    return '/Index/Main';
  }
  if (currentPath === '/Index/KnowledgeBase') { // 知识库管理
    return '/Index/KnowledgeBase';
  }
  if (currentPath === '/Index/QaRecords') { // 问答记录与分析
    return '/Index/QaRecords';
  }
  if (currentPath === '/Index/ModelConfig') { // 模型配置
    return '/Index/ModelConfig';
  }
  // 【修改】新增的管理员测试对话路径
  if (currentPath === '/Index/AITestChat') { // 智能体对话（测试）
    return '/Index/AITestChat';
  }
  // 【修改】新增的普通用户智能咨询路径
  if (currentPath === '/Index/SmartConsult') { // 智能咨询
    return '/Index/SmartConsult';
  }
  // 【修改】将其他用户菜单项路径也统一到 /Index 下
  if (currentPath === '/Index/faq') { // 常见问题
    return '/Index/faq';
  }
  if (currentPath === '/Index/my-consult-history') { // 我的咨询记录
    return '/Index/my-consult-history';
  }
  if (currentPath === '/Index/settings') { // 个人设置
    return '/Index/settings';
  }
  if (currentPath === '/Index/contact-support') { // 联系客服
    return '/Index/contact-support';
  }

  return currentPath;
});

const handleMenuItemSelect = (index) => {
  router.push(index);
};

const canSeeAdminFeatures = computed(() => {
  return currentUserRole.value === 'admin' || currentUserRole.value === 'super_admin';
});

const isNormalUser = computed(() => {
  return currentUserRole.value === 'user';
});
</script>

<template>
  <div class="sidebar-container" :class="{ 'is-collapsed': isCollapse }">
    <div class="logo-container">
      <el-icon v-if="!isCollapse" class="logo-icon">
        <Monitor />
      </el-icon>
      <span v-if="!isCollapse" class="logo-text">招生咨询系统</span>
      <el-icon v-else class="logo-icon-small">
        <Monitor />
      </el-icon>
    </div>

    <el-scrollbar>
      <el-menu
          :collapse="isCollapse"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          :collapse-transition="false"
          :default-active="activeMenuIndex"
          @select="handleMenuItemSelect"
          class="custom-menu"
      >
        <!-- 管理员/超级管理员菜单项 -->
        <template v-if="canSeeAdminFeatures">
          <!-- 首页 (管理员仪表盘) -->
          <el-menu-item index="/Index" class="menu-item">
            <el-icon class="menu-icon"><HomeFilled /></el-icon>
            <template #title>
              <span class="menu-text">管理员仪表盘</span>
            </template>
          </el-menu-item>

          <el-sub-menu index="system-management" class="menu-sub">
            <template #title>
              <el-icon class="menu-icon"><Setting /></el-icon>
              <span class="menu-text">系统管理</span>
            </template>
            <el-menu-item index="/Index/Main" class="menu-item">
              <el-icon class="menu-icon"><User /></el-icon>
              <span class="menu-text">用户管理</span>
            </el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="ai-management" class="menu-sub">
            <template #title>
              <el-icon class="menu-icon"><Cpu /></el-icon>
              <span class="menu-text">智能问答管理</span>
            </template>
            <el-menu-item index="/Index/KnowledgeBase" class="menu-item">
              <el-icon class="menu-icon"><Collection /></el-icon>
              <span class="menu-text">知识库管理</span>
            </el-menu-item>
            <el-menu-item index="/Index/QaRecords" class="menu-item">
              <el-icon class="menu-icon"><TrendCharts /></el-icon>
              <span class="menu-text">问答记录与分析</span>
            </el-menu-item>
            <el-menu-item index="/Index/ModelConfig" class="menu-item">
              <el-icon class="menu-icon"><Setting /></el-icon>
              <span class="menu-text">模型配置</span>
            </el-menu-item>
            <!-- 【修改】新增：智能体对话（测试） -->
            <el-menu-item index="/Index/AITestChat" class="menu-item">
              <el-icon class="menu-icon"><ChatDotSquare /></el-icon>
              <span class="menu-text">智能体对话（测试）</span>
            </el-menu-item>
          </el-sub-menu>
        </template>

        <!-- 普通用户菜单项 -->
        <template v-else-if="isNormalUser">
          <!-- 用户首页 -->
          <el-menu-item index="/Index/UserDashboard" class="menu-item">
            <el-icon class="menu-icon"><HomeFilled /></el-icon>
            <template #title>
              <span class="menu-text">用户首页</span>
            </template>
          </el-menu-item>

          <!-- 【修改】智能咨询 (核心功能) -->
          <el-menu-item index="/Index/SmartConsult" class="menu-item">
            <el-icon class="menu-icon"><ChatDotSquare /></el-icon>
            <template #title>
              <span class="menu-text">智能咨询</span>
            </template>
          </el-menu-item>

          <!-- 【修改】常见问题 -->
          <el-menu-item index="/Index/faq" class="menu-item">
            <el-icon class="menu-icon"><QuestionFilled /></el-icon>
            <template #title>
              <span class="menu-text">常见问题</span>
            </template>
          </el-menu-item>

          <!-- 【修改】我的咨询记录 -->
          <el-menu-item index="/Index/my-consult-history" class="menu-item">
            <el-icon class="menu-icon"><Tickets /></el-icon>
            <template #title>
              <span class="menu-text">我的咨询记录</span>
            </template>
          </el-menu-item>

          <!-- 【修改】个人设置 (可选，如果用户有个人信息管理页面) -->
          <el-menu-item index="/Index/settings" class="menu-item">
            <el-icon class="menu-icon"><Setting /></el-icon>
            <template #title>
              <span class="menu-text">个人设置</span>
            </template>
          </el-menu-item>

          <!-- 【修改】联系客服 (可选) -->
          <el-menu-item index="/Index/contact-support" class="menu-item">
            <el-icon class="menu-icon"><Service /></el-icon>
            <template #title>
              <span class="menu-text">联系客服</span>
            </template>
          </el-menu-item>
        </template>

        <!-- 如果还有其他通用菜单项，可以在这里添加，不加 v-if -->
      </el-menu>
    </el-scrollbar>

    <div class="sidebar-footer">
      <el-icon class="settings-icon"><Setting /></el-icon>
      <span v-if="!isCollapse" class="settings-text">设置</span>
    </div>
  </div>
</template>

<style scoped>
.sidebar-container {
  height: 100%;
  width: 220px;
  transition: width 0.3s ease;
  background-color: #304156;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.35);
  position: relative;
  z-index: 10;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-container.is-collapsed {
  width: 64px;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
  overflow: hidden;
  position: relative;
  transition: all 0.3s;
}

.logo-icon {
  font-size: 28px;
  color: #409EFF;
}

.logo-icon-small {
  font-size: 24px;
  color: #409EFF;
}

.logo-text {
  margin-left: 12px;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  background: linear-gradient(45deg, #409EFF, #36d1dc);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.el-scrollbar {
  flex: 1;
  overflow-x: hidden;
}

.custom-menu {
  border-right: none;
  padding-top: 10px;
}

.menu-item {
  height: 56px !important;
  line-height: 56px !important;
}

.menu-icon {
  font-size: 18px !important;
  margin-right: 10px;
}

.menu-text {
  font-size: 16px !important;
  font-weight: 500;
}

.el-menu:not(.el-menu--collapse) {
  width: 220px;
}

.el-menu-item.is-active {
  background-color: #263445 !important;
  position: relative;
}

.el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: #409EFF;
}

.el-sub-menu__title {
  height: 56px !important;
  line-height: 56px !important;
}

.el-menu-item:hover, .el-sub-menu__title:hover {
  background-color: #263445 !important;
}

.sidebar-footer {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
  color: #bfcbd9;
  cursor: pointer;
  transition: all 0.3s;
}

.sidebar-footer:hover {
  background-color: #1f2d3d;
  color: #fff;
}

.settings-icon {
  font-size: 18px;
}

.settings-text {
  margin-left: 8px;
  font-size: 14px;
}
</style>