// main.js
import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/theme-chalk/dark/css-vars.css' // 导入 Element Plus 的暗黑模式样式
import axios from 'axios' // 导入 axios
import router from './router' // 导入您的路由实例
import { ElMessage } from 'element-plus'; // 导入 ElMessage 用于错误提示

// 导入 Element Plus 的中文语言包
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const app = createApp(App)

// --- 注册 Element Plus ---
app.use(ElementPlus, {
    locale: zhCn, // 设置为中文语言包
})

// --- 注册 ElementPlus 图标 ---
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

// --- 配置 axios ---
// 【保持为 Java 后端地址】
axios.defaults.baseURL = "http://localhost:8090";

app.config.globalProperties.$axios = axios;
app.config.globalProperties.$httpUrl = "http://localhost:8090";

// --- Axios 请求拦截器 ---
axios.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = 'Bearer ' + token;
        }
        return config;
    },
    error => {
        console.error('Axios 请求拦截器错误:', error);
        return Promise.reject(error);
    }
);

// --- Axios 响应拦截器 ---
axios.interceptors.response.use(
    response => {
        return response;
    },
    error => {
        if (error.response && (error.response.status === 401 || error.response.status === 403)) {
            console.error('认证失败或Token过期，请重新登录。');
            ElMessage.error('登录状态已失效，请重新登录！');
            localStorage.removeItem('token');
            localStorage.removeItem('CurUser');
            sessionStorage.removeItem('CurUser');
            router.push('/login');
        }
        return Promise.reject(error);
    }
);

// --- 注册 Vue Router ---
app.use(router)

// --- 挂载 Vue 应用 ---
app.mount('#app')