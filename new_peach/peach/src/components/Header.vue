<template>
  <!-- 头部容器，动态绑定暗黑模式类名 -->
  <div class="header-container" :class="{ 'dark-mode': isDarkMode }">
    <!-- 左侧区域：包含折叠按钮 -->
    <div class="left-section">
      <!-- 带工具提示的折叠按钮 -->
      <el-tooltip :content="isCollapse ? '展开' : '折叠'" placement="bottom">
        <!-- 动态切换折叠/展开图标，并绑定点击事件 -->
        <el-icon class="fold-icon" @click="emit('toggle-collapse')">
          <component :is="isCollapse ? Expand : Fold" />
        </el-icon>
      </el-tooltip>
    </div>

    <!-- 中间区域留空 -->
    <div class="center-section"></div>

    <!-- 右侧功能区域 -->
    <div class="right-section">
      <!-- 搜索框 -->
      <div class="search-box">
        <el-input
            placeholder="搜索..."
            prefix-icon="Search"
            size="small"
            clearable
        />
      </div>

      <!-- 主题切换按钮 -->
      <div class="theme-switch" @click="toggleDarkMode">
        <el-tooltip :content="isDarkMode ? '切换到亮色模式' : '切换到暗色模式'" placement="bottom">
          <!-- 动态切换白天/夜晚图标 -->
          <el-icon class="theme-icon">
            <component :is="isDarkMode ? Sunny : Moon" />
          </el-icon>
        </el-tooltip>
      </div>

      <!-- 通知图标带消息提示 -->
      <div class="notification">
        <el-badge is-dot>
          <el-icon><Bell /></el-icon>
        </el-badge>
      </div>

      <!-- 用户信息下拉菜单 -->
      <div class="user-section">
        <el-dropdown trigger="click">
          <!-- 用户信息触发区域 -->
          <div class="user-dropdown-trigger">
            <!-- 用户头像 -->
            <el-avatar
                :size="32"
                src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"
            />
            <!-- 用户名，现在绑定到 user.name -->
            <span class="username">{{ user.name }}</span>
            <!-- 下拉箭头 -->
            <el-icon class="dropdown-icon">
              <ArrowDown />
            </el-icon>
          </div>
          <!-- 下拉菜单内容 -->
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goToPersonalCenter">
                <el-icon><User /></el-icon>
                <span>个人中心</span>
              </el-dropdown-item>
              <el-dropdown-item divided @click="logout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
// 组合式API引入
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'

// 引入Element Plus图标
import {
  Fold, Expand, Search, Bell,
  ArrowDown, User, SwitchButton,
  Moon, Sunny
} from '@element-plus/icons-vue'

// 获取路由实例
const router = useRouter()

// 组件属性定义
const props = defineProps({
  isCollapse: Boolean // 侧边栏折叠状态
})

// 定义事件发射器
const emit = defineEmits(['toggle-collapse'])

// 暗黑模式状态
const isDarkMode = ref(false)

// 用户信息状态
const user = ref({ name: '访客' });

// 切换主题方法
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  applyDarkMode(isDarkMode.value)
  // 保存主题设置到本地存储，使用'theme'作为key
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
}

// 应用主题到HTML根元素
const applyDarkMode = (isDark) => {
  if (isDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

// 加载用户数据方法
const loadUserData = () => {
  let storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
  if (storedUser) {
    try {
      const parsedUser = JSON.parse(storedUser);
      if (typeof parsedUser === 'object' && parsedUser !== null && parsedUser.name) {
        user.value = parsedUser;
      } else {
        user.value = { name: '未知用户' };
      }
    } catch (e) {
      console.error('解析用户数据失败:', e);
      user.value = { name: '数据错误' };
    }
  } else {
    user.value = { name: '访客' };
  }
};

// 退出登录方法
const logout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
      .then(() => {
        localStorage.removeItem('CurUser');
        sessionStorage.removeItem('CurUser');
        router.replace('/login');
        ElMessage.success('已成功退出登录！');
      })
      .catch(() => {
        ElMessage.info('已取消退出操作。');
      });
};

// 跳转到个人中心
const goToPersonalCenter = () => {
  router.push('/Index/Home');
};


// 监听系统主题变化的回调
const systemThemeChangeHandler = (e) => {
  // 仅在未手动设置主题时跟随系统
  if (!localStorage.getItem('theme')) {
    isDarkMode.value = e.matches;
    applyDarkMode(e.matches);
  }
};

// 组件挂载时
onMounted(() => {
  // --- 主题初始化 ---
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    // 优先使用本地存储的设置
    isDarkMode.value = savedTheme === 'dark';
  } else {
    // 否则，检测系统主题设置
    isDarkMode.value = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  applyDarkMode(isDarkMode.value);

  // --- 用户信息加载 ---
  loadUserData();

  // --- 监听系统主题变化 ---
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', systemThemeChangeHandler);
  // 在组件卸载时移除监听器
  onUnmounted(() => {
    mediaQuery.removeEventListener('change', systemThemeChangeHandler);
  });
});

</script>

<style scoped>
/* 头部容器基础样式 */
.header-container {
  height: 60px; /* 固定高度 */
  display: flex;
  align-items: center;
  justify-content: space-between; /* 三栏布局 */
  padding: 0 20px; /* 水平内边距 */
  background-color: #fff; /* 默认背景色 */
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08); /* 底部阴影 */
  position: relative;
  z-index: 999; /* 确保在最上层 */
  transition: background-color 0.3s, color 0.3s; /* 颜色过渡动画 */
}

/* 暗黑模式样式 - 直接通过父组件的类名控制 */
.dark .header-container, /* 当html.dark时应用 */
.header-container.dark-mode { /* 保持原有的本地class控制，提供双重保障 */
  background-color: #1e1e2e; /* 深色背景 */
  color: #cdd6f4; /* 浅色文字 */
  box-shadow: 0 1px 4px rgba(27, 33, 123, 0.5); /* 深色阴影 */
}

/* 左侧区域 */
.left-section {
  display: flex;
  align-items: center;
}

/* 右侧功能区域布局 */
.right-section {
  display: flex;
  align-items: center;
  gap: 20px; /* 元素间距 */
}

/* 用户信息触发区域样式 */
.user-dropdown-trigger {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown-trigger:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark .user-dropdown-trigger:hover,
.dark-mode .user-dropdown-trigger:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

/* 用户名样式 */
.username {
  margin: 0 8px;
  font-size: 14px;
}

/* 主题切换按钮样式 */
.theme-switch {
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: background-color 0.3s;
}

.theme-switch:hover {
  background-color: #f5f7fa;
}

.dark .theme-switch:hover,
.dark-mode .theme-switch:hover {
  background-color: #3a3a5a;
}

/* 图标过渡效果 */
.fold-icon, .theme-icon, .dropdown-icon {
  transition: color 0.3s;
  font-size: 20px;
}

.fold-icon {
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.3s, transform 0.3s;
}

.fold-icon:hover {
  transform: scale(1.1);
}

/* 通知图标 */
.notification {
  cursor: pointer;
}
</style>