<template>
  <div class="app-layout" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <div class="sidebar">
      <div class="sidebar-header">
        <h2 v-if="!isSidebarCollapsed" class="sidebar-title">Chat</h2>
        <!-- 收起/展开按钮移动到 sidebar-header 内部 -->
        <el-button link class="menu-toggle-btn-in-header" @click="toggleSidebar">
          <el-icon v-if="!isSidebarCollapsed"><Fold /></el-icon>
          <el-icon v-else><Expand /></el-icon>
          <!-- 展开时显示文字，收起时隐藏 -->
          <span v-if="!isSidebarCollapsed" class="menu-toggle-text">收起</span>
        </el-button>
      </div>
      <div class="new-chat-button-wrapper">
        <el-tooltip :content="'新建对话 (Ctrl K)'" placement="right" :disabled="!isSidebarCollapsed" effect="dark">
          <el-button type="primary" class="new-chat-btn" @click="startNewSession">
            <el-icon><Plus /></el-icon>
            <template v-if="!isSidebarCollapsed">
              新建对话
              <span class="hotkey">Ctrl K</span>
            </template>
          </el-button>
        </el-tooltip>
      </div>
      <div class="session-list custom-scrollbar">
        <template v-if="!isSidebarCollapsed">
          <template v-if="sortedChatSessions.length > 0">
            <div class="session-group-title">最近会话</div>
            <div v-for="session in sortedChatSessions" :key="session.id" class="session-item" :class="{ 'active': session.id === currentSessionId, 'is-pinned': session.isPinned }" @click="loadSession(session.id)">
              <!-- 新增 session-header 容器 -->
              <div class="session-header">
                <div class="session-title">{{ session.title }}</div>
                <div class="session-actions">
                  <el-button link class="session-action-btn" @click.stop="deleteSession(session.id)"><el-icon><Delete /></el-icon></el-button>
                  <!-- 置顶/取消置顶按钮 -->
                  <el-button link class="session-action-btn" @click.stop="togglePinSession(session.id)">
                    <el-tooltip :content="session.isPinned ? '取消置顶' : '置顶'" placement="top" effect="dark">
                      <el-icon v-if="session.isPinned"><Download /></el-icon>
                      <el-icon v-else><Upload /></el-icon>
                    </el-tooltip>
                  </el-button>
                </div>
              </div>
              <div class="session-preview">{{ session.lastMessagePreview }}</div>
            </div>
          </template>
          <template v-else>
            <div class="no-sessions-placeholder">暂无会话，点击“新建对话”开始聊天吧！</div>
          </template>
        </template>
        <template v-else>
          <div class="collapsed-sessions-list custom-scrollbar">
            <el-tooltip v-for="session in topNSessions" :key="session.id" :content="session.title" placement="right" effect="dark">
              <div class="collapsed-session-item" :class="{ 'active': session.id === currentSessionId, 'is-pinned': session.isPinned }" @click="loadSession(session.id)">
                <el-avatar :size="32" class="collapsed-session-avatar">{{ session.title ? session.title.charAt(0).toUpperCase() : '?' }}</el-avatar>
              </div>
            </el-tooltip>
          </div>
        </template>
      </div>
      <!-- sidebar-footer 移除 -->
    </div>
    <div class="chat-container">
      <div class="app-header">
        <div class="header-content">
          <h1 class="app-title">AI招生咨询</h1>
          <div class="status-area">
            <el-tag :type="theme === 'dark' ? 'primary' : 'success'" size="small" effect="dark" class="status-tag"><el-icon class="status-icon"><SuccessFilled /></el-icon>在线</el-tag>
          </div>
        </div>
      </div>
      <div class="main-content-wrapper">
        <div v-if="messages.length === 1 && messages[0].sender === 'ai'" class="empty-chat-container">
          <div class="empty-chat-content">
            <h1 class="empty-chat-title">AI招生咨询</h1>
            <p class="empty-chat-subtitle">你好！我是小招，有什么可以帮助你解答吗？</p>
            <div class="suggestion-buttons">
              <el-button class="suggestion-btn" round @click="quickSendMessage('本科招生流程')">本科招生流程</el-button>
              <el-button class="suggestion-btn" round @click="quickSendMessage('有什么专业')">有什么专业？</el-button>
              <el-button class="suggestion-btn" round @click="quickSendMessage('校园环境怎么样')">校园环境怎么样？</el-button>
            </div>
          </div>
        </div>
        <div v-else class="message-area custom-scrollbar" ref="messageArea">
          <div v-for="message in messages" :key="message.id" class="message-wrapper" :class="message.sender">
            <template v-if="message.sender === 'ai'">
              <el-avatar class="avatar" :class="message.sender"><el-icon><Cpu /></el-icon></el-avatar>
              <div class="message-content-group">
                <div class="message-bubble" :class="message.sender">
                  <div v-if="message.isLoading" class="loading-indicator"><el-icon class="loading-icon"><Loading /></el-icon><span>AI正在思考中...</span></div>
                  <div v-else class="message-content" v-html="formatMessageContent(message.content)"></div>
                  <div v-if="!message.isLoading" class="message-actions-bar">
                    <el-tooltip content="满意" placement="top" effect="dark">
                      <!-- This SVG matches the 'Thumbs Up' icon you provided -->
                      <el-button link class="action-bar-btn" :class="{ 'feedback-selected-like': message.feedback === 'like' }" @click="submitFeedback(message.id, 'like')">
                        <svg xmlns="http://www.w3.org/2000/svg" class="custom-feedback-icon" viewBox="0 0 24 24">
                          <path d="M7 10v12"></path>
                          <path d="M15 5.433A2.4 2.4 0 0 1 17.4 3h1.2a2.4 2.4 0 0 1 2.4 2.4V12a2.4 2.4 0 0 1-2.4 2.4h-3.6l-3.25 6.5A2.4 2.4 0 0 1 9.6 22H4.4a2.4 2.4 0 0 1-2.4-2.4v-8.4a2.4 2.4 0 0 1 2.4-2.4h3.6Z"></path>
                        </svg>
                      </el-button>
                    </el-tooltip>
                    <el-tooltip content="不满意" placement="top" effect="dark">
                      <!-- This SVG matches the 'Thumbs Down' icon you provided -->
                      <el-button link class="action-bar-btn" :class="{ 'feedback-selected-dislike': message.feedback === 'dislike' }" @click="submitFeedback(message.id, 'dislike')">
                        <svg xmlns="http://www.w3.org/2000/svg" class="custom-feedback-icon" viewBox="0 0 24 24">
                          <path d="M7 14V2"></path>
                          <path d="M15 18.567A2.4 2.4 0 0 0 17.4 21h1.2a2.4 2.4 0 0 0 2.4-2.4V12a2.4 2.4 0 0 0-2.4-2.4h-3.6l-3.25-6.5A2.4 2.4 0 0 0 9.6 2H4.4a2.4 2.4 0 0 0-2.4 2.4v8.4A2.4 2.4 0 0 0 4.4 15h3.6Z"></path>
                        </svg>
                      </el-button>
                    </el-tooltip>
                    <el-tooltip content="复制" placement="top" effect="dark">
                      <el-button link class="action-bar-btn" @click="copyMessageContent(message.content)"><el-icon><DocumentCopy /></el-icon></el-button>
                    </el-tooltip>
                    <el-tooltip content="删除" placement="top" effect="dark">
                      <el-button link class="action-bar-btn" @click="deleteMessage(message.id)"><el-icon><Delete /></el-icon></el-button>
                    </el-tooltip>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="message-content-group">
                <div class="message-bubble" :class="message.sender">
                  <div class="message-content" v-html="formatMessageContent(message.content)"></div>
                  <div v-if="!message.isLoading" class="message-actions-bar">
                    <el-tooltip content="复制" placement="top" effect="dark">
                      <el-button link class="action-bar-btn" @click="copyMessageContent(message.content)"><el-icon><DocumentCopy /></el-icon></el-button>
                    </el-tooltip>
                    <el-tooltip content="删除" placement="top" effect="dark">
                      <el-button link class="action-bar-btn" @click="deleteMessage(message.id)"><el-icon><Delete /></el-icon></el-button>
                    </el-tooltip>
                  </div>
                </div>
              </div>
              <el-avatar class="avatar" :class="message.sender"><el-icon><UserFilled /></el-icon></el-avatar>
            </template>
          </div>
        </div>
        <div class="input-wrapper">
          <div class="input-container">
            <el-input v-model="inputText" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" placeholder="输入您的问题..." class="input-field" @keydown.enter.exact.prevent="sendMessage" />
            <el-button type="primary" class="send-btn" :disabled="!inputText.trim()" @click="sendMessage"><el-icon class="send-icon"><Promotion /></el-icon></el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Promotion, Loading, SuccessFilled,
  UserFilled, Refresh, Cpu, DocumentCopy,
  Fold, Expand, Plus, Delete, Upload, Download
} from '@element-plus/icons-vue'
import axios from 'axios'
import { useRouter } from 'vue-router';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const router = useRouter();

const inputText = ref('')
const messageArea = ref(null)
const currentSessionId = ref(null);
const userId = ref(null);
const theme = ref('light');
const chatSessions = reactive([]);

const quickSendMessage = (text) => {
  inputText.value = text;
  sendMessage();
}
const messages = computed(() => {
  const activeSession = chatSessions.find(s => s.id === currentSessionId.value);
  return activeSession ? activeSession.messages : [];
});

const sortedChatSessions = computed(() => {
  return [...chatSessions].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    return b.lastActivity - a.lastActivity;
  });
});

const isSidebarCollapsed = ref(false);
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};
const topNSessionsLimit = 10;
const topNSessions = computed(() => {
  return sortedChatSessions.value.slice(0, topNSessionsLimit);
});

const deleteMessage = (messageId) => {
  const activeSession = chatSessions.find(s => s.id === currentSessionId.value);
  if (!activeSession) return;
  ElMessageBox.confirm('确定要删除这条消息吗？此操作不可撤销。', '提示', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning', customClass: 'message-box-custom'
  }).then(() => {
    const messageIndex = activeSession.messages.findIndex(m => m.id === messageId);
    if (messageIndex !== -1) {
      activeSession.messages.splice(messageIndex, 1);
      ElMessage.success('消息已删除');
    }
  }).catch(() => {});
};

const syncThemeState = () => {
  const globalTheme = localStorage.getItem('theme');
  theme.value = globalTheme === 'dark' ? 'dark' : 'light';
  document.documentElement.classList.toggle('dark', theme.value === 'dark');
};
const handleStorageChange = (event) => {
  if (event.key === 'theme') { syncThemeState(); }
};

const formatMessageContent = (text) => {
  if (!text) return '';
  let processedText = text;
  processedText = processedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  const lines = processedText.split('\n');
  let htmlOutput = '';
  let inUnorderedList = false;
  let inOrderedList = false;
  lines.forEach(line => {
    const trimmedLine = line.trim();
    const numberedBoldParagraphMatch = trimmedLine.match(/^(\d+\.\s*[^:]+:\s*)(.*)/);
    if (numberedBoldParagraphMatch) {
      if (inUnorderedList) { htmlOutput += '</ul>'; inUnorderedList = false; }
      if (inOrderedList) { htmlOutput += '</ol>'; inOrderedList = false; }
      const boldPart = numberedBoldParagraphMatch[1];
      const contentPart = numberedBoldParagraphMatch[2];
      htmlOutput += `<p><strong>${boldPart}</strong>${contentPart}</p>`;
      return;
    }
    const headingMatch = trimmedLine.match(/^(#+)\s*(.*)/);
    if (headingMatch) {
      if (inUnorderedList) { htmlOutput += '</ul>'; inUnorderedList = false; }
      if (inOrderedList) { htmlOutput += '</ol>'; inOrderedList = false; }
      const headingText = headingMatch[2];
      htmlOutput += `<p class="message-heading"><strong>${headingText}</strong></p>`;
      return;
    }
    const unorderedListItemMatch = trimmedLine.match(/^[\*\-]\s*(.*)/);
    if (unorderedListItemMatch) {
      if (!inUnorderedList) { htmlOutput += '<ul>'; inUnorderedList = true; }
      if (inOrderedList) { htmlOutput += '</ol>'; inOrderedList = false; }
      htmlOutput += `<li><span class="bullet-point">&bull;</span> ${unorderedListItemMatch[1]}</li>`;
      return;
    }
    const orderedListItemMatch = trimmedLine.match(/^(\d+)\.\s*(.*)/);
    if (orderedListItemMatch) {
      if (!inOrderedList) { htmlOutput += '<ol>'; inOrderedList = true; }
      if (inUnorderedList) { htmlOutput += '</ul>'; inUnorderedList = false; }
      htmlOutput += `<li>${orderedListItemMatch[1]}. ${orderedListItemMatch[2]}</li>`;
      return;
    }
    if (inUnorderedList) { htmlOutput += '</ul>'; inUnorderedList = false; }
    if (inOrderedList) { htmlOutput += '</ol>'; inOrderedList = false; }
    if (trimmedLine === '') {
      htmlOutput += '<p>&nbsp;</p>';
    } else {
      htmlOutput += `<p>${line}</p>`;
    }
  });
  if (inUnorderedList) { htmlOutput += '</ul>'; }
  if (inOrderedList) { htmlOutput += '</ol>'; }
  return htmlOutput;
};

const copyMessageContent = async (contentToCopy) => {
  if (contentToCopy) {
    try {
      const plainTextContent = contentToCopy
          .replace(/\*\*(.*?)\*\*/g, '$1')
          .replace(/^(#+)\s*(.*)/gm, '$2')
          .replace(/^[\*\-]\s*(.*)/gm, '$1')
          .replace(/^(\d+)\.\s*(.*)/gm, '$1. $2');
      await navigator.clipboard.writeText(plainTextContent);
      ElMessage.success('内容已复制到剪贴板！');
    } catch (err) {
      console.error('复制失败:', err);
      ElMessage.error('复制失败，请手动复制。');
    }
  }
};

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || !currentSessionId.value || userId.value === null) {
    if (userId.value === null) {
      ElMessage.warning('用户未登录，无法发送消息。请先登录。');
      router.replace('/login');
    } else {
      ElMessage.warning('请输入消息内容。');
    }
    return;
  }
  const activeSession = chatSessions.find(s => s.id === currentSessionId.value);
  if (!activeSession) return;

  activeSession.messages.push({
    id: `user-${Date.now()}`,
    sender: 'user',
    content: text,
    isLoading: false,
    feedback: null
  });

  if (activeSession.messages.filter(m => m.sender === 'user').length === 1) {
    activeSession.title = text.length > 20 ? text.substring(0, 20) + '...' : text;
  }
  activeSession.lastActivity = Date.now();

  activeSession.messages.push({
    id: `ai-loading-${Date.now()}`,
    sender: 'ai',
    content: '',
    isLoading: true,
    feedback: null
  });
  inputText.value = '';
  scrollToBottom();
  await getAIResponseFromBackend(text);
}

const getAIResponseFromBackend = async (userInput) => {
  const activeSession = chatSessions.find(s => s.id === currentSessionId.value);
  if (!activeSession || userId.value === null) {
    if (userId.value === null) {
      ElMessage.warning('用户未登录，无法获取AI响应。请先登录。');
      router.replace('/login');
    }
    return;
  }
  try {
    const response = await axios.post(`${API_BASE_URL}/chat`, {
      message: userInput, session_id: currentSessionId.value, user_id: userId.value
    }, { headers: { 'Content-Type': 'application/json' } });

    const lastLoadingIndex = activeSession.messages.findLastIndex(m => m.isLoading);
    if (lastLoadingIndex !== -1) {
      activeSession.messages[lastLoadingIndex] = {
        id: response.data.message_id,
        sender: 'ai',
        content: response.data.response,
        isLoading: false,
        feedback: null
      };
      activeSession.lastMessagePreview = response.data.response.length > 50 ? response.data.response.substring(0, 50) + '...' : response.data.response;
      scrollToBottom();
    }
  } catch (error) {
    console.error('Error fetching AI response:', error);
    const errorMessage = error.response?.data?.detail || 'AI服务暂时不可用，请稍后再试。';
    const lastLoadingIndex = activeSession.messages.findLastIndex(m => m.isLoading);
    if (lastLoadingIndex !== -1) {
      activeSession.messages[lastLoadingIndex] = { sender: 'ai', content: `抱歉，AI服务出现问题：${errorMessage}`, isLoading: false };
      activeSession.lastMessagePreview = `抱歉，AI服务出现问题：${errorMessage}`;
      scrollToBottom();
    } else {
      activeSession.messages.push({ sender: 'ai', content: `抱歉，AI服务出现问题：${errorMessage}`, isLoading: false });
      activeSession.lastMessagePreview = `抱歉，${errorMessage}`;
      scrollToBottom();
    }
  }
}

const startNewSession = async () => {
  if (userId.value === null) {
    ElMessage.warning('用户未登录，无法创建新会话。请先登录。');
    router.replace('/login');
    return;
  }
  try {
    const response = await axios.post(`${API_BASE_URL}/new_session`, {
      user_id: userId.value
    }, { headers: { 'Content-Type': 'application/json' } });

    const newSessionId = response.data.session_id;
    const welcomeMessage = response.data.welcome_message;
    const welcomeMessageId = response.data.welcome_message_id;

    const newSession = reactive({
      id: newSessionId,
      title: '新会话',
      messages: [{
        id: welcomeMessageId,
        sender: 'ai',
        content: welcomeMessage,
        isLoading: false,
        feedback: null
      }],
      lastActivity: Date.now(),
      lastMessagePreview: welcomeMessage.length > 50 ? welcomeMessage.substring(0, 50) + '...' : welcomeMessage,
      isPinned: false
    });
    chatSessions.push(newSession);
    currentSessionId.value = newSessionId;
    scrollToBottom();
  } catch (error) {
    console.error('Error starting new session:', error);
    const errorMessage = error.response?.data?.detail || '无法开始新会话。请检查网络或联系管理员。';
    ElMessage.error(`无法创建新会话: ${errorMessage}`);
  }
}

const loadSession = async (sessionId) => {
  if (currentSessionId.value === sessionId) return;
  currentSessionId.value = sessionId;
  scrollToBottom();
}

const submitFeedback = async (messageId, feedbackType) => {
  const activeSession = chatSessions.find(s => s.id === currentSessionId.value);
  if (!activeSession) return;

  const message = activeSession.messages.find(m => m.id === messageId);
  if (!message) return;

  const originalFeedback = message.feedback;
  const newFeedback = originalFeedback === feedbackType ? null : feedbackType;

  message.feedback = newFeedback;

  try {
    await axios.post(`${API_BASE_URL}/feedback`, {
      message_id: messageId,
      session_id: currentSessionId.value,
      user_id: userId.value,
      feedback: newFeedback
    });
    ElMessage.success('感谢您的反馈！');
  } catch (error) {
    console.error('Error submitting feedback:', error);
    ElMessage.error('提交反馈失败，请稍后再试。');
    message.feedback = originalFeedback;
  }
};

const savePinnedStateToLocalStorage = () => {
  const pinnedStates = chatSessions.reduce((acc, session) => {
    if (session.isPinned) {
      acc[session.id] = true;
    }
    return acc;
  }, {});
  localStorage.setItem('pinnedSessions', JSON.stringify(pinnedStates));
};

const loadPinnedStateFromLocalStorage = () => {
  const storedPinnedStates = localStorage.getItem('pinnedSessions');
  if (storedPinnedStates) {
    try {
      return JSON.parse(storedPinnedStates);
    } catch (e) {
      console.error("Error parsing pinned sessions from localStorage:", e);
      return {};
    }
  }
  return {};
};

const togglePinSession = (sessionId) => {
  const session = chatSessions.find(s => s.id === sessionId);
  if (session) {
    session.isPinned = !session.isPinned;
    savePinnedStateToLocalStorage();
    ElMessage.success(session.isPinned ? '会话已置顶' : '会话已取消置顶');
  }
};

const deleteSession = async (sessionIdToDelete) => {
  if (userId.value === null) {
    ElMessage.warning('用户未登录，无法删除会话。请先登录。');
    router.replace('/login');
    return;
  }
  try {
    await ElMessageBox.confirm('确定要删除此会话吗？此操作不可撤销。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    await axios.delete(`${API_BASE_URL}/session/${sessionIdToDelete}?user_id=${userId.value}`);
    const index = chatSessions.findIndex(s => s.id === sessionIdToDelete);
    if (index !== -1) {
      chatSessions.splice(index, 1);
      savePinnedStateToLocalStorage();
      ElMessage.success('会话已成功删除！');
      if (currentSessionId.value === sessionIdToDelete) {
        if (chatSessions.length > 0) {
          currentSessionId.value = sortedChatSessions.value[0].id;
          scrollToBottom();
        } else {
          await startNewSession();
        }
      }
    }
  } catch (error) {
    if (error === 'cancel') {
      ElMessage.info('已取消删除操作');
    } else {
      console.error('删除会话失败:', error);
      const errorMessage = error.response?.data?.detail || '删除会话失败，请稍后再试。';
      ElMessage.error(errorMessage);
    }
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messageArea.value) {
      messageArea.value.scrollTop = messageArea.value.scrollHeight
    }
  })
}
watch(messages, scrollToBottom, { deep: true })
watch(currentSessionId, scrollToBottom)

onMounted(async () => {
  syncThemeState();
  window.addEventListener('storage', handleStorageChange);
  const token = localStorage.getItem('token');
  const storedUserJson = localStorage.getItem('CurUser') || sessionStorage.getItem('CurUser');
  if (token && storedUserJson) {
    try {
      const storedUser = JSON.parse(storedUserJson);
      if (storedUser && storedUser.id) {
        userId.value = storedUser.id;
      } else {
        localStorage.removeItem('token');
        localStorage.removeItem('CurUser');
        sessionStorage.removeItem('CurUser');
        ElMessage.error('登录信息已过期或损坏，请重新登录。');
        router.replace('/login');
        return;
      }
    } catch (e) {
      localStorage.removeItem('token');
      localStorage.removeItem('CurUser');
      sessionStorage.removeItem('CurUser');
      ElMessage.error('登录信息已损坏，请重新登录。');
      router.replace('/login');
      return;
    }
  } else {
    ElMessage.info('请先登录以查看或创建会话。');
    router.replace('/login');
    return;
  }
  const storedPinnedStates = loadPinnedStateFromLocalStorage();
  if (userId.value) {
    try {
      const sessionsResponse = await axios.get(`${API_BASE_URL}/user_sessions/${userId.value}`);
      const fetchedSessionInfos = sessionsResponse.data;
      if (fetchedSessionInfos.length > 0) {
        for (const sessionInfo of fetchedSessionInfos) {
          const historyResponse = await axios.get(`${API_BASE_URL}/history/${sessionInfo.session_id}?user_id=${userId.value}`);
          const messagesForSession = historyResponse.data;

          let sessionTitle = '新会话';
          let lastMessagePreview = '';
          if (messagesForSession.length > 0) {
            const firstUserMessage = messagesForSession.find(m => m.sender === 'user');
            if (firstUserMessage) {
              sessionTitle = firstUserMessage.content.length > 20 ? firstUserMessage.content.substring(0, 20) + '...' : firstUserMessage.content;
            } else {
              const firstAiMessage = messagesForSession.find(m => m.sender === 'ai');
              if (firstAiMessage) { sessionTitle = firstAiMessage.content.length > 20 ? firstAiMessage.content.substring(0, 20) + '...' : firstAiMessage.content; }
            }
            const lastMessage = messagesForSession[messagesForSession.length - 1];
            lastMessagePreview = lastMessage.content.length > 50 ? lastMessage.content.substring(0, 50) + '...' : lastMessage.content;
          }
          chatSessions.push(reactive({
            id: sessionInfo.session_id,
            title: sessionTitle,
            messages: messagesForSession.map(msg => ({ ...msg, isLoading: false })),
            lastActivity: new Date(sessionInfo.created_at).getTime(),
            lastMessagePreview: lastMessagePreview,
            isPinned: !!storedPinnedStates[sessionInfo.session_id]
          }));
        }
        if (sortedChatSessions.value.length > 0) {
          currentSessionId.value = sortedChatSessions.value[0].id;
          scrollToBottom();
        }
      } else {
        await startNewSession();
      }
    } catch (error) {
      console.error('Error loading user sessions or history:', error);
      ElMessage.error('加载历史会话失败，将为您创建新会话。');
      await startNewSession();
    }
  } else {
    ElMessage.info('用户未登录，请先登录。');
    router.replace('/login');
  }
});

onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange);
});
</script>

<style scoped>
/* CSS 变量部分 */
.app-layout {
  --chat-bg: #F0F2F5; /* 浅色模式主背景 */
  --main-card-bg: #FFFFFF; /* 浅色模式卡片/侧边栏背景 */
  --header-text: #333;
  --header-border: #E0E0E0;
  --ai-bubble-bg: #F7F7F8;
  --ai-bubble-text: #333;
  --user-bubble-bg: #D4E8FF;
  --user-bubble-text: #333;
  --ai-avatar-bg: #E6F0FF;
  --ai-avatar-icon: #2563eb;
  --user-avatar-bg: #E0E0E0;
  --user-avatar-icon: #666;
  --input-wrapper-bg: var(--main-card-bg);
  --input-container-bg: #FFFFFF;
  --input-field-bg: #F0F2F5;
  --input-field-text: #333;
  --input-field-border: #DCDFE6;
  --placeholder-text: #A8A8A8;
  --send-btn-bg: #2563eb;
  --send-btn-text: white;
  --send-btn-disabled-bg: #a0cfff;
  --action-bar-bg: #FFFFFF;
  --action-bar-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  --action-bar-icon-color: #606266;
  --action-bar-icon-hover-bg: #f5f5f5;
  --main-card-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  --loading-text: #718096;
  --status-tag-bg: #67c23a;
  --sidebar-bg: var(--main-card-bg);
  --sidebar-border-color: #E0E0E0;
  --sidebar-header-text: #333;
  --sidebar-icon-color: #666;
  --new-chat-btn-bg: #2563eb;
  --new-chat-btn-text: white;
  --new-chat-btn-hover-bg: #1d4ed8;
  --session-item-hover-bg: #F0F0F0;
  --session-item-active-bg: #E6F0FF;
  --session-item-active-text: #1d4ed8;
  --session-title-text: #333;
  --session-preview-text: #666;
  --session-action-btn-color: #999;
  --session-action-btn-hover-bg: rgba(0, 0, 0, 0.1);
  --scrollbar-thumb-bg: #c1c1c1;
  --scrollbar-thumb-hover-bg: #a8a8a8;
  --scrollbar-track-bg: transparent;
  --sidebar-collapsed-width: 60px; /* 调整：侧边栏收起后的宽度，更窄 */
  --primary-accent: #4361ee;
  --primary-accent-rgb: 67, 97, 238;
  --card-elevation: 0 8px 30px rgba(0,0,0,0.08);
  --input-focus-glow: 0 4px 15px rgba(67, 97, 238, 0.2);
  --button-hover-scale: 1.05;
}

/* 暗色模式变量 (参考设计图调整) */
html.dark .app-layout {
  --chat-bg: #18191a; /* 主背景色，非常深 */
  --main-card-bg: #242526; /* 卡片/侧边栏背景，略浅于主背景 */
  --header-text: #E4E6EB; /* 浅色文字 */
  --header-border: #3A3B3C; /* 深色边框 */
  --ai-bubble-bg: #3A3B3C; /* AI 气泡背景色 */
  --ai-bubble-text: #E4E6EB; /* AI 气泡文字色 */
  --user-bubble-bg: #3A3B3C; /* 用户气泡背景色，与 AI 气泡保持一致 */
  --user-bubble-text: #E4E6EB; /* 用户气泡文字色 */
  --ai-avatar-bg: #3A3B3C; /* AI 头像背景色 */
  --ai-avatar-icon: #E4E6EB; /* AI 头像图标色 */
  --user-avatar-bg: #3A3B3C; /* 用户头像背景色 */
  --user-avatar-icon: #E4E6EB; /* 用户头像图标色 */
  --input-wrapper-bg: var(--main-card-bg); /* 输入区域背景，与卡片背景一致，实现扁平化 */
  --input-container-bg: var(--main-card-bg); /* 输入框容器背景 */
  --input-field-bg: #3A3B3C; /* 输入框内部背景，更深的灰色 */
  --input-field-text: #E4E6EB; /* 输入框文字色 */
  --input-field-border: transparent; /* 无边框 */
  --placeholder-text: #8A8D91; /* 占位符文字色 */
  --send-btn-bg: #555555; /* 发送按钮背景色 */
  --send-btn-text: #E4E6EB; /* 发送按钮图标色 */
  --send-btn-disabled-bg: #777777; /* 禁用状态背景色 */
  --action-bar-bg: #4a4d50; /* 操作栏背景色 */
  --action-bar-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); /* 操作栏阴影 */
  --action-bar-icon-color: #E4E6EB; /* 操作栏图标色 */
  --action-bar-icon-hover-bg: #5f6266; /* 操作栏图标悬停背景色 */
  --main-card-shadow: none; /* 暗色模式下移除卡片阴影，实现扁平化 */
  --loading-text: #AAAAAA;
  --status-tag-bg: #0084FF; /* 状态标签保持蓝色，提供对比度 */
  --sidebar-bg: var(--main-card-bg);
  --sidebar-border-color: #3A3B3C;
  --sidebar-header-text: #E4E6EB;
  --sidebar-icon-color: #B0B3B8;
  --new-chat-btn-bg: #555555; /* 新建对话按钮背景色，与发送按钮保持一致 */
  --new-chat-btn-text: white;
  --new-chat-btn-hover-bg: #666666;
  --session-item-hover-bg: #3A3B3C; /* 会话项悬停背景色 */
  --session-item-active-bg: #4A4A4A; /* 会话项激活背景色 */
  --session-item-active-text: #FFFFFF; /* 会话项激活文字色 */
  --session-title-text: #E4E6EB;
  --session-preview-text: #B0B3B8;
  --session-action-btn-color: #B0B3B8;
  --session-action-btn-hover-bg: #4A4A4A;
  --scrollbar-thumb-bg: #555;
  --scrollbar-thumb-hover-bg: #777;
  --primary-accent: #0084FF; /* 主强调色 */
  --primary-accent-rgb: 0, 132, 255;
  --card-elevation: none;
  --input-focus-glow: 0 4px 15px rgba(0, 132, 255, 0.4);
  --button-hover-scale: 1.05;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: var(--chat-bg);
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  transition: background-color 0.3s ease;
  padding: 0;
  box-sizing: border-box;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
  background-color: var(--sidebar-bg);
  border-radius: 12px;
  box-shadow: var(--main-card-shadow);
  margin-right: 15px;
  display: flex;
  flex-direction: column;
  padding: 15px;
  box-sizing: border-box;
  transition: width 0.3s ease, padding 0.3s ease, margin-right 0.3s ease, background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, border-radius 0.3s ease;
}
html.dark .sidebar {
  box-shadow: none;
  border-right: 1px solid var(--sidebar-border-color);
  border-radius: 0;
  margin-right: 0;
  padding: 15px;
}
.sidebar-header {
  flex-shrink: 0;
  padding-bottom: 8px;
  margin-bottom: 8px;
  min-height: 40px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--sidebar-border-color);
  justify-content: space-between;
}
.sidebar-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--sidebar-header-text);
  margin: 0;
  white-space: nowrap;
}

.menu-toggle-btn-in-header {
  color: var(--sidebar-icon-color);
  padding: 8px;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: all 0.2s ease;
  background-color: transparent;
}
.menu-toggle-btn-in-header.el-button.is-link:hover {
  background-color: var(--session-item-hover-bg);
  color: var(--sidebar-header-text);
}
.menu-toggle-btn-in-header .el-icon {
  font-size: 1.4rem;
  margin: 0;
}

.new-chat-button-wrapper {
  margin-bottom: 12px;
  flex-shrink: 0;
}
.new-chat-btn {
  width: 100%;
  justify-content: center;
  padding: 12px 15px;
  border-radius: 10px;
  font-size: 1rem;
  background-color: var(--new-chat-btn-bg);
  border-color: var(--new-chat-btn-bg);
  color: var(--new-chat-btn-text);
  transition: all 0.2s ease;
  position: relative;
  display: inline-flex;
  align-items: center;
}
.new-chat-btn:hover {
  background-color: var(--new-chat-btn-hover-bg);
  border-color: var(--new-chat-btn-hover-bg);
}
.new-cat-btn .el-icon {
  margin-right: 8px;
}
.hotkey {
  position: absolute;
  right: 15px;
  font-size: 0.8rem;
  opacity: 0.7;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 5px;
}
.session-group-title {
  font-size: 0.9rem;
  color: var(--placeholder-text);
  margin-top: 10px;
  margin-bottom: 5px;
  padding-left: 5px;
}
.session-item {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  margin-bottom: 4px;
  position: relative;
  overflow: hidden;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease, border 0.2s ease;
}
.session-item:hover {
  background-color: var(--session-item-hover-bg);
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}
html.dark .session-item:hover {
  box-shadow: none;
  transform: none;
}
.session-item.active {
  background-color: rgba(var(--primary-accent-rgb), 0.1);
  border-left: 4px solid var(--primary-accent);
  padding-left: 8px;
}
html.dark .session-item.active {
  background-color: rgba(var(--primary-accent-rgb), 0.2);
}
.session-item.active .session-title,
.session-item.active .session-preview,
.session-item.active .session-action-btn {
  color: var(--primary-accent);
}
html.dark .session-item.active .session-title,
html.dark .session-item.active .session-preview,
html.dark .session-item.active .session-action-btn {
  color: var(--session-item-active-text);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 4px;
}

.session-title {
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--session-title-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
  padding-right: 5px;
}
.session-preview {
  font-size: 0.92rem;
  color: var(--session-preview-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-actions {
  display: flex;
  gap: 5px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  flex-shrink: 0;
}
.session-item:hover .session-actions {
  opacity: 1;
  pointer-events: auto;
}

.session-action-btn {
  font-size: 1rem;
  color: var(--session-action-btn-color);
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s ease, color 0.2s ease;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.session-action-btn:hover {
  background-color: var(--primary-accent);
  color: white !important;
}
html.dark .session-action-btn:hover {
  background-color: var(--primary-accent);
  color: white !important;
}

.no-sessions-placeholder {
  padding: 20px;
  text-align: center;
  color: var(--placeholder-text);
  font-size: 0.9rem;
}
.sidebar-footer {
  display: none;
}

.app-layout.sidebar-collapsed .sidebar {
  width: var(--sidebar-collapsed-width);
  padding: 15px 0;
  align-items: center;
}
html.dark .app-layout.sidebar-collapsed .sidebar {
  margin-right: 0;
}
.app-layout.sidebar-collapsed .sidebar-header {
  border-bottom: none;
  margin-bottom: 15px;
  padding-bottom: 0;
  min-height: 0;
  justify-content: center;
}
.app-layout.sidebar-collapsed .sidebar-title {
  display: none;
}

.app-layout.sidebar-collapsed .new-chat-button-wrapper {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}
.app-layout.sidebar-collapsed .new-chat-btn {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 50%;
  justify-content: center;
}
.app-layout.sidebar-collapsed .new-chat-btn .el-icon {
  margin-right: 0;
  font-size: 1.2rem;
}

.collapsed-sessions-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  width: 100%;
}
.collapsed-session-item {
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: background-color 0.2s ease, border 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}
.collapsed-session-item:hover {
  background-color: var(--session-item-hover-bg);
}
.collapsed-session-item.active {
  background-color: var(--session-item-active-bg);
  border: 2px solid var(--primary-accent);
  padding: 3px;
}
.collapsed-session-avatar {
  background-color: var(--ai-avatar-bg);
  color: var(--ai-avatar-icon);
  font-size: 1rem;
  font-weight: bold;
  transition: background-color 0.2s ease, color 0.2s ease;
}
html.dark .collapsed-session-avatar {
  background-color: var(--ai-bubble-bg);
  color: var(--ai-bubble-text);
}
html.dark .collapsed-session-item.active .collapsed-session-avatar {
  background-color: var(--primary-accent);
  color: white;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--main-card-bg);
  border-radius: 12px;
  box-shadow: var(--main-card-shadow);
  overflow: hidden;
  transition: background-color 0.3s ease, border-radius 0.3s ease, box-shadow 0.3s ease;
  padding: 0;
}
html.dark .chat-container {
  border-radius: 0;
  box-shadow: none;
}
.app-header {
  background-color: var(--main-card-bg);
  color: var(--header-text);
  height: 60px;
  z-index: 10;
  flex-shrink: 0;
  border-bottom: 1px solid var(--header-border);
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
html.dark .app-header {
  background-color: var(--chat-bg);
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}
.app-title {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
}
.status-area {
  display: flex;
  align-items: center;
  gap: 10px;
}
.status-tag {
  background-color: var(--status-tag-bg);
  border-color: var(--status-tag-bg);
}

.main-content-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  background-color: var(--main-card-bg);
  overflow: hidden;
  transition: background-color 0.3s ease;
  height: 100%;
}
html.dark .main-content-wrapper {
  background-color: var(--chat-bg);
}

.empty-chat-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 10px 20px;
}

.empty-chat-content {
  max-width: 600px;
}
.empty-chat-title {
  font-size: 2.8rem;
  font-weight: bold;
  color: var(--header-text);
  margin-bottom: 8px;
}
html.dark .empty-chat-title {
  color: #E4E6EB;
}
.empty-chat-subtitle {
  font-size: 1.1rem;
  color: var(--session-preview-text);
  margin-bottom: 15px;
}
.suggestion-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}
.suggestion-btn {
  background-color: var(--ai-bubble-bg);
  border-color: var(--header-border);
  color: var(--ai-bubble-text);
  padding: 8px 16px;
  font-size: 0.9rem;
}
html.dark .suggestion-btn {
  background-color: var(--ai-bubble-bg);
  border-color: var(--ai-bubble-bg);
  color: var(--ai-bubble-text);
}
.suggestion-btn:hover {
  background-color: var(--session-item-hover-bg);
  border-color: var(--session-item-hover-bg);
}

.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 5px 15px;
  display: flex;
  flex-direction: column;
}
.message-wrapper {
  position: relative;
  display: flex;
  align-items: flex-start;
  max-width: 85%;
  margin-bottom: 5px;
  margin-top: 5px;
}
.message-wrapper.user {
  justify-content: flex-end;
  margin-left: auto;
}
.message-wrapper.ai {
  justify-content: flex-start;
  margin-right: auto;
}
.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  font-size: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--ai-avatar-bg);
  color: var(--ai-avatar-icon);
  transition: background-color 0.3s ease, color 0.3s ease;
}
.message-wrapper.ai .avatar {
  margin-right: 8px;
}
.message-wrapper.user .avatar {
  background-color: var(--user-avatar-bg);
  color: var(--user-avatar-icon);
  margin-left: 8px;
  order: 2;
}
.message-content-group {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.message-wrapper.user .message-content-group {
  align-items: flex-end;
}
.message-bubble {
  position: relative;
  padding: 8px 12px;
  padding-bottom: 8px;
  border-radius: 10px;
  line-height: 1.4;
  word-break: break-word;
  background-color: var(--ai-bubble-bg);
  color: var(--ai-bubble-text);
  transition: background-color 0.3s ease, color 0.3s ease;
}
.message-bubble.user {
  background-color: var(--user-bubble-bg);
  color: var(--user-bubble-text);
}

.message-content {
  font-size: 0.95rem;
  color: inherit;
}
.message-content p {
  margin: 0 0 0.3em 0;
}
.message-content p:last-child {
  margin-bottom: 0;
}
.loading-indicator {
  display: flex;
  align-items: center;
  color: var(--loading-text);
  font-size: 0.85rem;
}
.loading-icon {
  margin-right: 6px;
  animation: rotating 1.5s linear infinite;
}
@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
.message-actions-bar {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background-color: var(--action-bar-bg);
  border-radius: 4px;
  padding: 0px;
  display: flex;
  gap: 2px;
  box-shadow: var(--action-bar-shadow);
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  z-index: 1;
}
.message-bubble:hover .message-actions-bar {
  opacity: 1;
  visibility: visible;
}
.action-bar-btn {
  font-size: 1rem; /* Adjust size for better SVG visibility */
  color: var(--action-bar-icon-color);
  padding: 3px;
  border-radius: 3px;
  transition: background-color 0.2s ease, color 0.2s ease;
  display: flex; /* Ensure SVG is centered */
  align-items: center;
  justify-content: center;
}
.action-bar-btn:hover {
  background-color: var(--action-bar-icon-hover-bg);
}

.input-wrapper {
  flex-shrink: 0;
  padding: 10px 15px;
  background: var(--input-wrapper-bg);
  border-top: 1px solid var(--header-border);
  transition: background 0.3s ease, border-top-color 0.3s ease;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px;
  border-radius: 12px;
  background: var(--input-container-bg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.3s ease;
}
html.dark .input-container {
  box-shadow: none;
  border: 1px solid var(--header-border);
}
.input-container:focus-within {
  box-shadow: var(--input-focus-glow);
}
html.dark .input-container:focus-within {
  box-shadow: 0 4px 15px rgba(0, 132, 255, 0.4);
}

.input-field {
  flex: 1;
}
.input-field :deep(.el-textarea__inner) {
  background-color: var(--input-field-bg);
  color: var(--input-field-text);
  min-height: 48px !important;
  padding: 12px 16px;
  font-size: 1.05rem;
  border: none;
  border-radius: 12px;
  box-shadow: none;
  resize: none;
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
html.dark .input-field :deep(.el-textarea__inner) {
  background-color: transparent;
  border: none;
}
.input-field :deep(.el-textarea__inner:focus) {
  border-color: transparent;
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background-color: var(--send-btn-bg);
  color: var(--send-btn-text);
  border: none;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  flex-shrink: 0;
}
.send-btn:hover:not([disabled]) {
  transform: scale(var(--button-hover-scale));
  box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
}
html.dark .send-btn:hover:not([disabled]) {
  box-shadow: 0 4px 12px rgba(0, 132, 255, 0.4);
}
.send-btn[disabled] {
  opacity: 0.5;
  transform: none !important;
  box-shadow: none !important;
}
.send-icon {
  font-size: 1.4rem;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: var(--scrollbar-track-bg);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: var(--scrollbar-thumb-bg);
  border-radius: 10px;
  border: 2px solid var(--scrollbar-track-bg);
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: var(--scrollbar-thumb-hover-bg);
}
.custom-scrollbar::-webkit-scrollbar-button {
  display: none;
}

/* Styles for custom SVG feedback icons */
.custom-feedback-icon {
  width: 1em;
  height: 1em;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: fill 0.2s ease, stroke 0.2s ease;
}

.action-bar-btn.feedback-selected-like,
.action-bar-btn.feedback-selected-like:hover {
  color: #67c23a; /* Green for 'like' */
}

.action-bar-btn.feedback-selected-dislike,
.action-bar-btn.feedback-selected-dislike:hover {
  color: #f56c6c; /* Red for 'dislike' */
}

/* Fill the icon when its feedback type is selected */
.action-bar-btn.feedback-selected-like .custom-feedback-icon,
.action-bar-btn.feedback-selected-dislike .custom-feedback-icon {
  fill: currentColor;
  stroke-width: 1.5; /* Slightly thinner stroke when filled */
}

@media (max-width: 768px) {
  html {
    font-size: 15px;
  }
  .app-layout {
    flex-direction: column;
    padding: 0;
  }
  .sidebar {
    width: 100%;
    height: auto;
    border-radius: 0;
    box-shadow: none;
    margin-right: 0;
    border-bottom: 1px solid var(--sidebar-border-color);
  }
  .session-list {
    display: flex;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  .session-item {
    flex-shrink: 0;
    width: 180px;
    margin-right: 10px;
  }
  .app-layout.sidebar-collapsed .sidebar {
    display: none;
  }
  .message-wrapper {
    max-width: 90%;
  }
  .message-area {
    padding-bottom: 0;
  }
  .input-wrapper {
    padding: 10px 15px;
  }
  .input-container {
    padding: 5px;
    border-radius: 15px;
  }
  .input-field :deep(.el-textarea__inner) {
    min-height: 40px !important;
    padding: 8px 14px;
    font-size: 0.95rem;
  }
  .send-btn {
    width: 44px;
    height: 44px;
    border-radius: 10px;
  }
}
</style>