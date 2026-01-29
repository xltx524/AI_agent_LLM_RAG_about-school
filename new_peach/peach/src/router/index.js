// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import { ElMessage } from 'element-plus';

import Login from '../components/Login.vue';
import Index from '../components/Index.vue';
import Home from '../components/Self information.vue'; // 注意文件名中的空格，如果可以，建议重命名
import Main from '../components/Main.vue';
import Register from '../components/Register.vue';

import AdminDashboard from '../components/Dashboard.vue';
import UserDashboard from '../components/UserDashboard.vue';
import ChatTalk from '../components/ChatTalk.vue';
import KnowledgeBaseManagement from '../components/KnowledgeBaseManagement.vue';
import QaAnalytics from '../components/QaAnalytics.vue'; // <--- 新增：导入 QaAnalytics 组件


const PlaceholderPage = {
    template: `
    <div style="padding: 20px; text-align: center; font-size: 20px; color: #666; background-color: #f0f2f5; border-radius: 8px; margin: 20px;">
      <p style="font-size: 24px; font-weight: bold; color: #409EFF;">页面建设中...</p>
      <p style="font-size: 16px;">当前路径: <code style="background-color: #e0e0e0; padding: 3px 6px; border-radius: 4px;">{{ $route.path }}</code></p>
      <p style="margin-top: 15px;">敬请期待！</p>
    </div>
  `
};


const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { title: '用户登录', requiresAuth: false }
    },
    {
        path: '/register',
        name: 'Register',
        component: Register,
        meta: { title: '用户注册', requiresAuth: false }
    },
    {
        path: '/Index',
        name: 'IndexWrapper',
        component: Index,
        meta: { title: '系统首页', requiresAuth: true },
        children: [
            {
                path: '', // 访问 /Index 时默认加载
                name: 'AdminDashboard',
                component: AdminDashboard,
                meta: { title: '管理员仪表盘', requiresAuth: true, roles: ['admin', 'super_admin'] }
            },
            {
                path: 'UserDashboard', // 访问 /Index/UserDashboard 时加载
                name: 'UserDashboard',
                component: UserDashboard,
                meta: { title: '用户首页', requiresAuth: true, roles: ['user'] }
            },
            {
                path: 'Home',
                name: 'SelfInformation', // 个人中心
                component: Home,
                meta: { title: '个人中心', requiresAuth: true }
            },
            {
                path: 'Main',
                name: 'UserManagement', // 用户管理
                component: Main,
                meta: { title: '用户管理', requiresAuth: true, roles: ['admin', 'super_admin'] }
            },
            {
                path: 'KnowledgeBase',
                name: 'KnowledgeBase',
                component: KnowledgeBaseManagement,
                meta: { title: '知识库管理', requiresAuth: true, roles: ['admin', 'super_admin'] }
            },
            {
                path: 'AITestChat',
                name: 'AITestChat',
                component: ChatTalk,
                meta: { title: '智能体对话（测试）', requiresAuth: true, roles: ['admin', 'super_admin'] }
            },
            {
                path: 'QaRecords',
                name: 'QaRecords',
                component: QaAnalytics, // <--- 修改：使用 QaAnalytics 组件
                meta: { title: '问答记录与分析', requiresAuth: true, roles: ['admin', 'super_admin'] }
            },
            {
                path: 'ModelConfig',
                name: 'ModelConfig',
                component: PlaceholderPage,
                meta: { title: '模型配置', requiresAuth: true, roles: ['admin', 'super_admin'] }
            },
            {
                path: 'SmartConsult',
                name: 'SmartConsult',
                component: ChatTalk,
                meta: { title: '智能咨询', requiresAuth: true, roles: ['user'] }
            },
            {
                path: 'faq',
                name: 'FAQ',
                component: PlaceholderPage,
                meta: { title: '常见问题', requiresAuth: true, roles: ['user'] }
            },
            {
                path: 'my-consult-history',
                name: 'MyConsultHistory',
                component: PlaceholderPage,
                meta: { title: '我的咨询记录', requiresAuth: true, roles: ['user'] }
            },
            {
                path: 'settings',
                name: 'UserSettings',
                component: Home,
                meta: { title: '个人设置', requiresAuth: true, roles: ['user'] }
            },
            {
                path: 'contact-support',
                name: 'ContactSupport',
                component: PlaceholderPage,
                meta: { title: '联系客服', requiresAuth: true, roles: ['user'] }
            },
        ]
    },
    {
        path: '/',
        redirect: (to) => {
            const storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
            // 同样检查 token 是否存在
            const token = localStorage.getItem('token');

            if (token && storedUser) { // 只有当 token 和用户数据都存在时才尝试解析
                try {
                    const user = JSON.parse(storedUser);
                    const userRole = user.role;
                    if (userRole === 'admin' || userRole === 'super_admin') {
                        return '/Index';
                    } else if (userRole === 'user') {
                        return '/Index/UserDashboard';
                    } else {
                        console.warn('Redirect: 未知用户角色，请重新登录。');
                        localStorage.removeItem('token'); // 清除 token
                        localStorage.removeItem('CurUser');
                        sessionStorage.removeItem('CurUser');
                        return '/login';
                    }
                } catch (e) {
                    console.error("Redirect: 解析用户数据失败:", e);
                    localStorage.removeItem('token'); // 清除 token
                    localStorage.removeItem('CurUser');
                    sessionStorage.removeItem('CurUser');
                    return '/login';
                }
            }
            // 如果 token 或用户数据缺失，则重定向到登录页
            localStorage.removeItem('token'); // 清除可能残留的 token
            localStorage.removeItem('CurUser');
            sessionStorage.removeItem('CurUser');
            return '/login';
        }
    },
    { path: '/:pathMatch(.*)*', name: 'NotFound', redirect: '/Index' }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

// 全局前置守卫
router.beforeEach((to, from, next) => {
    document.title = to.meta.title ? `${to.meta.title} - 协和学院招生系统` : '协和学院招生系统';

    const token = localStorage.getItem('token'); // <-- 获取 JWT Token
    const storedUser = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
    let isAuthenticated = false;
    let userRole = null;

    // 只有当 JWT Token 和用户数据都存在时，才认为是已认证状态
    if (token && storedUser) {
        try {
            const user = JSON.parse(storedUser);
            isAuthenticated = true;
            userRole = user.role;
            console.log(`Router Guard: User authenticated. Role: ${userRole}. Navigating to: ${to.path}`);
        } catch (e) {
            console.error("Router Guard: 从存储中解析用户数据时出错:", e);
            // 如果解析失败，清除所有相关存储并标记为未认证
            localStorage.removeItem('token');
            localStorage.removeItem('CurUser');
            sessionStorage.removeItem('CurUser');
            isAuthenticated = false;
        }
    } else {
        // 如果 token 或用户数据缺失，则清除所有相关存储并标记为未认证
        localStorage.removeItem('token');
        localStorage.removeItem('CurUser');
        sessionStorage.removeItem('CurUser');
        console.log(`Router Guard: User not authenticated. Navigating to: ${to.path}`);
    }

    // 1. 处理已登录用户尝试访问 /login 页面
    if (to.path === '/login' && isAuthenticated) {
        if (userRole === 'admin' || userRole === 'super_admin') {
            ElMessage.info('您已登录，正在跳转到管理员首页！');
            next('/Index');
        } else if (userRole === 'user') {
            ElMessage.info('您已登录，正在跳转到用户首页！');
            next('/Index/UserDashboard');
        } else {
            ElMessage.warning('您已登录，但用户角色未知，请重新登录！');
            localStorage.removeItem('token'); // 清除 token
            localStorage.removeItem('CurUser');
            sessionStorage.removeItem('CurUser');
            next('/login');
        }
        return;
    }

    // 处理已登录用户尝试访问 /register 页面
    if (to.path === '/register' && isAuthenticated) {
        ElMessage.info('您已登录，无需重复注册！');
        if (userRole === 'admin' || userRole === 'super_admin') {
            next('/Index');
        } else if (userRole === 'user') {
            next('/Index/UserDashboard');
        } else {
            next('/');
        }
        return;
    }

    // 2. 处理需要认证的页面 (requiresAuth: true)
    if (to.meta.requiresAuth) {
        if (!isAuthenticated) {
            ElMessage.warning('请先登录才能访问此页面！');
            next({ path: '/login', query: { redirect: to.fullPath } });
            return;
        }

        // 3. 处理角色权限 (meta.roles 存在)
        if (to.meta.roles) {
            console.log(`Router Guard: Route requires roles: ${to.meta.roles}. Current user role: ${userRole}.`);

            if (!userRole) {
                ElMessage.error('无法获取您的用户角色，请重新登录或联系管理员！');
                localStorage.removeItem('token'); // 清除 token
                localStorage.removeItem('CurUser');
                sessionStorage.removeItem('CurUser');
                next('/login');
                return;
            }

            if (!to.meta.roles.includes(userRole)) {
                ElMessage.error('您没有权限访问此页面！');
                if (userRole === 'user') {
                    if (to.name !== 'UserDashboard') {
                        next('/Index/UserDashboard');
                    } else {
                        console.error("Router Guard: User already on UserDashboard but permission denied. Forcing re-login.");
                        localStorage.removeItem('token'); // 清除 token
                        localStorage.removeItem('CurUser');
                        sessionStorage.removeItem('CurUser');
                        next('/login');
                    }
                } else if (userRole === 'admin' || userRole === 'super_admin') {
                    if (to.name !== 'AdminDashboard') {
                        next('/Index');
                    } else {
                        console.error("Router Guard: User already on AdminDashboard but permission denied. Forcing re-login.");
                        localStorage.removeItem('token'); // 清除 token
                        localStorage.removeItem('CurUser');
                        sessionStorage.removeItem('CurUser');
                        next('/login');
                    }
                } else {
                    ElMessage.error('未知用户角色，无权限访问，请重新登录！');
                    localStorage.removeItem('token'); // 清除 token
                    localStorage.removeItem('CurUser');
                    sessionStorage.removeItem('CurUser');
                    next('/login');
                }
                return;
            }
        }
    }

    // 4. 其他情况，允许导航
    next();
});

// 全局后置守卫，用于设置页面标题
router.afterEach((to, from) => {
    document.title = to.meta.title ? `${to.meta.title} - 协和学院招生系统` : '协和学院招生系统';
    console.log(`Router AfterEach: Setting document.title to: "${document.title}" for route: ${to.path}`);
});


export default router;