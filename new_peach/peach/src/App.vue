<script setup>
import Index from './components/Index.vue'
</script>

<template>
  <div class="app">
    <router-view/>
  </div>

</template>

<style scoped>
/* 在App.vue的<style>部分或全局CSS文件中 */
:root {
  --background-color: #ffffff;
  --text-color: #333333;
  --border-color: #e4e7ed;
  --hover-color: #f5f7fa;
  --header-bg: #ffffff;
  --sidebar-bg: #f5f7fa;
  --card-bg: #ffffff;
  --main-content-bg: #ffffff;
}

html.dark {
  /* 基于Claude界面的深色主题 */
  --background-color: #1E1E1E;       /* 主背景色 - 深灰色 */
  --sidebar-bg: #2D2D2D;             /* 侧边栏背景 - 稍浅的深灰色 */
  --main-content-bg: #1E1E1E;        /* 主内容区域背景 - 深灰色 */
  --header-bg: #2D2D2D;              /* 头部背景 - 与侧边栏一致 */
  --card-bg: #2D2D2D;                /* 卡片背景 - 稍浅的深灰色 */
  --hover-color: #3A3A3A;            /* 悬停颜色 - 中灰色 */
  --border-color: #444444;           /* 边框颜色 - 中灰色 */
  --text-color: #E0E0E0;             /* 文字颜色 - 浅灰色 */
  --secondary-text-color: #AAAAAA;   /* 次要文字颜色 - 中灰色 */

  /* 强调色 */
  --primary-color: #7C8AFF;          /* 主要强调色 - 紫蓝色 */
  --success-color: #4CAF50;          /* 成功色 - 绿色 */
  --warning-color: #FFC107;          /* 警告色 - 黄色 */
  --danger-color: #F44336;           /* 危险色 - 红色 */
  --info-color: #29B6F6;             /* 信息色 - 浅蓝色 */

  /* 代码块背景 */
  --code-bg: #2D2D2D;                /* 代码块背景 - 稍浅的深灰色 */
  --code-border: #444444;            /* 代码块边框 - 中灰色 */
}

/* 主内容区域背景色修改 */
html.dark body,
html.dark #app,
html.dark .app-container,
html.dark .main-container,
html.dark .main-content {
  background-color: var(--main-content-bg) !important;
  color: var(--text-color);
}

/* 侧边栏样式 */
html.dark .sidebar,
html.dark .el-menu,
html.dark .el-menu--vertical,
html.dark .el-aside {
  background-color: var(--sidebar-bg) !important;
  border-right-color: var(--border-color);
}

/* 表格样式修改 */
html.dark .el-table {
  background-color: var(--card-bg) !important;
  --el-table-bg-color: var(--card-bg) !important;
  --el-table-tr-bg-color: var(--card-bg) !important;
  --el-table-border-color: var(--border-color);
  --el-table-header-bg-color: #3A3A3A; /* 表头稍微深一点 */
  --el-table-header-text-color: var(--text-color);
  --el-table-text-color: var(--text-color);
}

/* 表格行样式 */
html.dark .el-table tr {
  background-color: var(--card-bg) !important;
}

/* 表格单元格样式 */
html.dark .el-table td.el-table__cell,
html.dark .el-table th.el-table__cell {
  background-color: var(--card-bg) !important;
}

/* 表格斑马纹样式 */
html.dark .el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background-color: #333333 !important;
}

/* 表格行悬停样式 */
html.dark .el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell {
  background-color: var(--hover-color) !important;
}

/* 卡片样式 */
html.dark .el-card {
  --el-card-bg-color: var(--card-bg) !important;
  border-color: var(--border-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* 输入框样式 */
html.dark .el-input__inner,
html.dark .el-textarea__inner {
  background-color: #333333;
  border-color: var(--border-color);
  color: var(--text-color);
}

html.dark .el-input__inner:focus,
html.dark .el-textarea__inner:focus {
  border-color: var(--primary-color);
}

/* 按钮样式 */
html.dark .el-button {
  background-color: #3A3A3A;
  border-color: var(--border-color);
  color: var(--text-color);
}

html.dark .el-button:hover {
  background-color: #444444;
}

html.dark .el-button--primary {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

html.dark .el-button--primary:hover {
  background-color: #6B78E6; /* 稍浅的主色调 */
  border-color: #6B78E6;
}

/* 菜单项样式 */
html.dark .el-menu-item {
  color: var(--text-color);
}

html.dark .el-menu-item:hover {
  background-color: var(--hover-color);
}

html.dark .el-menu-item.is-active {
  color: var(--primary-color);
  background-color: #333333;
}

/* 代码块样式 */
html.dark pre,
html.dark code {
  background-color: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: 4px;
  color: #E0E0E0;
}

/* 滚动条样式 */
html.dark ::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

html.dark ::-webkit-scrollbar-track {
  background: #2D2D2D;
}

html.dark ::-webkit-scrollbar-thumb {
  background: #555555;
  border-radius: 4px;
}

html.dark ::-webkit-scrollbar-thumb:hover {
  background: #666666;
}

/* 对话框样式 */
html.dark .el-dialog {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

html.dark .el-dialog__title {
  color: var(--text-color);
}

html.dark .el-dialog__body {
  color: var(--text-color);
}

/* 下拉菜单样式 */
html.dark .el-dropdown-menu {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3);
}

html.dark .el-dropdown-menu__item {
  color: var(--text-color);
}

html.dark .el-dropdown-menu__item:hover {
  background-color: var(--hover-color);
}

/* 标签页样式 */
html.dark .el-tabs__item {
  color: var(--secondary-text-color);
}

html.dark .el-tabs__item.is-active {
  color: var(--primary-color);
}

html.dark .el-tabs__active-bar {
  background-color: var(--primary-color);
}

html.dark .el-tabs__nav-wrap::after {
  background-color: var(--border-color);
}
</style>