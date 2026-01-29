<script setup>
import { ref } from 'vue'
// 以下图标在 Header 和 Aside 中使用，如果 Index 不直接使用可以不在这里导入，但通常为了方便管理会保留
import { Menu as IconMenu, Message, Setting, ArrowDown } from '@element-plus/icons-vue'

import Aside from "./Aside.vue"; // 侧边栏组件
import Header from "./Header.vue"; // 头部组件
// import Main from "./Main.vue"; // Main 组件现在可能不再需要，或者其内容会成为 Index 的子路由

const isCollapse = ref(false)

const handleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// components:{Aside, Header, Main} // 这行在 <script setup> 中是冗余的，可以删除
</script>

<template>
  <el-container class="layout-container-demo" style="height: 100vh;">
    <el-aside
        :width="isCollapse ? '64px' : '220px'"
        style="background-color: #304156; transition: width 0.3s;"
    >
      <Aside :is-collapse="isCollapse" />
    </el-aside>

    <el-container>
      <el-header style="height: 64px; padding: 0 20px; border-bottom: 1px solid #eee;">
        <Header
            :is-collapse="isCollapse"
            @toggle-collapse="handleCollapse"
        />
      </el-header>

      <el-main style="padding: 20px;">
        <!-- 这里是关键：子路由将在这里渲染 -->
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-container-demo .el-aside {
  overflow: hidden;
}
/* 如果你想让整个布局填充视口，可以给 .layout-container-demo 添加样式 */
.layout-container-demo {
  width: 100%;
  height: 100vh; /* 确保容器高度占满视口 */
}
</style>