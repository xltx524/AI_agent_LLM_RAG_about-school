本项目设计并实现了一个基于Agentic RAG架构的协和学院招生咨询智能体，旨在通过知识图谱（Neo4j）与非结构化文档检索（RAG）的深度融合，有效解决传统大模型在处理招生分数、学费等精确数据时产生的“幻觉”与逻辑断裂问题。系统采用Vue3、Spring Boot、FastAPI及讯飞星火大模型构建，其核心亮点在于双路检索机制：利用Text-to-Cypher技术实现结构化事实的精准遍历，并结合向量检索补全政策细节，从而为考生和家长提供既有准确事实支撑、又具备可视化图表展示的7×24小时专业咨询服务，显著提升了高校招生工作的智能化水平与信息准确度。
ai_chatbot_backend为后端fastAPI部分通过调用LLM大语言模型进行回答用户的提问，new_peach为前后端，前后端进行了分离，后端使用spring boot，前端使用vue3 + element ui 设计
效果图片如下
后台统计数据图片
<img width="763" height="400" alt="8e27d10e9fc64fad32168dc2db83c35a" src="https://github.com/user-attachments/assets/4c10e1b0-a810-46d7-b7ab-bc0343f3066b" />
知识库管理图片
<img width="784" height="471" alt="161d1f7c02cc4d1127609bea925a00d4" src="https://github.com/user-attachments/assets/94d9a16d-0e0c-4909-bfea-1953a9d85906" />
后台数据处理
<img width="2444" height="480" alt="5b89e83863e4e2a9bca726bf50591e5c" src="https://github.com/user-attachments/assets/825d0cdf-9b63-4436-8eac-53bd14706707" />
