import os
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Union, Optional
from pathlib import Path
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

from fastapi.staticfiles import StaticFiles

from sparkai.llm.llm import ChatSparkLLM
from sparkai.core.messages import ChatMessage

from dotenv import load_dotenv

from sqlalchemy.orm import Session as DBSession, aliased
from sqlalchemy import func, distinct
from database import User, Session as DBSessionModel, Message as DBMessageModel, KnowledgeEntry, create_db_tables, \
    get_db

# --- 导入知识抽取相关的模块 ---
from knowledge_extractor.text_processor import get_text_from_file, clean_text, segment_sentences, load_spacy_model
from knowledge_extractor.ner_re_pipeline import init_ner_re_components, extract_entities, extract_relations
from knowledge_extractor.neo4j_handler import get_neo4j_driver, import_extracted_data_to_neo4j, close_neo4j_driver
from knowledge_extractor.config import SPACY_MODEL_NAME

# --- 【新增】导入图谱查询服务 ---
# 确保 graph_service_simple.py 在同一目录下，且环境已安装 langchain 等依赖
try:
    from graph_service_simple import query_graph
except ImportError:
    print("警告: 未找到 graph_service_simple 模块或依赖缺失，图谱问答功能将不可用。")


    def query_graph(query):
        return None

load_dotenv()

# --- 讯飞星火大模型配置 ---
SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'
SPARKAI_APP_ID = os.getenv('SPARKAI_APP_ID')
SPARKAI_API_SECRET = os.getenv('SPARKAI_API_SECRET')
SPARKAI_API_KEY = os.getenv('SPARKAI_API_KEY')
SPARKAI_DOMAIN = '4.0Ultra'

# --- 知识库和LLM配置 ---
CONTACT_INFO = "电话：0591－22868770，邮箱：xhzs@fjnu.edu.cn"
SYSTEM_PROMPT = f"""你是一个专业的“福建师范大学协和学院AI招生咨询顾问”，名为“协和小智”。
你的主要职责是为潜在学生和家长提供关于福建师范大学协和学院招生政策、专业设置、校园生活、申请流程、收费标准等一切疑问的全面、准确、及时的官方信息。

你的回答必须：
1.  **基于提供的知识库内容**，绝不编造、猜测或虚构任何信息。如果知识库中没有相关信息，请礼貌地告知用户“很抱歉，我目前无法提供您所需的信息，建议您直接联系协和学院招生办公室（{CONTACT_INFO}）。”
2.  **语气专业、友好、耐心且积极**。
3.  **语言清晰、简洁、易懂**，避免使用复杂术语，或在必要时进行解释。
4.  **客观公正**，不带个人偏见。

你不能：
1.  提供个人建议、做出入学承诺或处理个人敏感信息。
2.  访问实时网络信息，你的知识仅限于内部知识库。

你的目标是帮助用户全面了解福建师范大学协和学院，解决他们的疑问，并鼓励他们进一步了解和申请。
"""

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'uploaded_knowledge_files'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

llm_instance: Union[ChatSparkLLM, None] = None

KNOWN_MAJORS = [
    "数字媒体技术", "通信工程", "网络工程", "物联网工程",
    "智能科学与技术", "电子信息工程", "计算机科学与技术",
    "法学", "金融学", "投资学", "金融工程",
    "财务管理", "工商管理", "人力资源管理", "市场营销",
    "物流管理", "物业管理", "国际金融实验班", "国际会计实验班",
    "广告学", "汉语言文学", "动画", "产品设计",
    "音乐表演", "休闲体育", "学前教育", "环境设计",
    "日语", "英语", "商务英语", "电子商务",
    "国际经济与贸易", "国际商务", "会展经济与管理"
]

KNOWN_DEPARTMENTS_MAJORS = {
    "信息技术系": [
        "数字媒体技术", "通信工程", "网络工程", "物联网工程",
        "智能科学与技术", "电子信息工程", "计算机科学与技术"
    ],
    "经济与法学系": [
        "法学", "金融学", "投资学", "金融工程"
    ],
    "管理学系": [
        "财务管理", "工商管理", "人力资源管理", "市场营销",
        "物流管理", "物业管理"
    ],
    "国际教育学院": [
        "国际金融实验班", "国际会计实验班"
    ],
    "文化产业系": [
        "广告学", "汉语言文学", "动画", "产品设计",
        "音乐表演", "休闲体育", "学前教育", "环境设计"
    ],
    "外语系": [
        "日语", "英语", "商务英语"
    ],
    "国际商学系": [
        "电子商务", "国际经济与贸易", "国际商务", "会展经济与管理"
    ]
}


# --- 知识处理/向量化（模拟） -> 知识抽取与图谱填充 ---
def process_knowledge_entry(knowledge_id: int, db: DBSession):
    try:
        entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == knowledge_id).first()
        if not entry:
            print(f"知识条目 {knowledge_id} 未找到，无法处理。")
            return

        # --- 文本提取 ---
        document_content = None
        source_file_path: Optional[Path] = None
        if entry.file_path:
            source_file_path = BASE_DIR / entry.file_path
            document_content = get_text_from_file(source_file_path)
            entry.source = '文件上传'
        elif entry.content:
            document_content = entry.content
            entry.source = '手动录入'

        if not document_content:
            entry.status = "failed"
            entry.processing_notes = "处理失败：无法提取内容。"
            db.add(entry)
            db.commit()
            db.refresh(entry)
            print(f"知识条目 {knowledge_id} ('{entry.title}') 处理失败：无法提取内容。")
            return

        entry.content = document_content  # 更新数据库中的完整文本内容，以便后续处理

        # --- 文本预处理 ---
        cleaned_text = clean_text(document_content)
        sentences = segment_sentences(cleaned_text)

        all_extracted_entities = []
        all_extracted_relations = []

        # --- NER & RE 流程 ---
        load_spacy_model(SPACY_MODEL_NAME)
        init_ner_re_components()

        for sent_text in sentences:
            doc = load_spacy_model()(sent_text)
            entities = extract_entities(sent_text)
            relations = extract_relations(doc, entities)

            all_extracted_entities.extend(entities)
            all_extracted_relations.extend(relations)

        # 对抽取结果进行最终去重和清洗
        final_entities = list({json.dumps(e, sort_keys=True, ensure_ascii=False) for e in all_extracted_entities})
        final_entities = [json.loads(s) for s in final_entities]

        final_relations = list({json.dumps(r, sort_keys=True, ensure_ascii=False) for r in all_extracted_relations})
        final_relations = [json.loads(s) for s in final_relations]

        extracted_kg_data = {"entities": final_entities, "relations": final_relations}

        print(
            f"知识条目 {knowledge_id} ('{entry.title}') 抽取到 {len(final_entities)} 实体, {len(final_relations)} 关系。")

        # --- 导入到 Neo4j ---
        import_extracted_data_to_neo4j(extracted_kg_data)

        entry.status = "processed"
        entry.processing_notes = "知识抽取并导入图谱成功。"
        print(f"知识条目 {knowledge_id} ('{entry.title}') 处理成功并导入Neo4j。")

        db.add(entry)
        db.commit()
        db.refresh(entry)

    except Exception as e:
        print(f"处理知识条目 {knowledge_id} 时发生错误: {e}")
        if entry:
            entry.status = "failed"
            entry.processing_notes = f"处理失败: {e}"
            db.add(entry)
            db.commit()
            db.refresh(entry)


# --- 1. 定义 Lifespan (替代 on_startup 和 on_shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # === 启动逻辑 (Startup) ===
    global llm_instance
    print("Initializing LLM and creating database tables...")

    create_db_tables()
    print("Database tables (sessions, messages, knowledge_entries) created/checked.")

    if not all([SPARKAI_APP_ID, SPARKAI_API_KEY, SPARKAI_API_SECRET]):
        print("警告：SparkAI 环境变量未完全设置，无法初始化 SparkAI 模型。请检查 .env 文件。")
        llm_instance = None
    else:
        llm_instance = ChatSparkLLM(
            spark_api_url=SPARKAI_URL,
            spark_app_id=SPARKAI_APP_ID,
            spark_api_key=SPARKAI_API_KEY,
            spark_api_secret=SPARKAI_API_SECRET,
            spark_llm_domain=SPARKAI_DOMAIN,
            streaming=False,
            request_timeout=60
        )
        print("SparkAI LLM initialized.")

    if llm_instance is None:
        raise RuntimeError("LLM instance could not be initialized. Check API keys and configurations.")

    load_spacy_model(SPACY_MODEL_NAME)
    init_ner_re_components()
    get_neo4j_driver()

    print("Knowledge Bases will be retrieved from database dynamically.")

    # === 分界线：应用运行中 ===
    yield

    # === 关闭逻辑 (Shutdown) ===
    close_neo4j_driver()
    print("Application shutdown: Neo4j driver closed.")


# --- FastAPI 应用 (应用 lifespan) ---
app = FastAPI(lifespan=lifespan)

# 配置 CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic 模型 (修复 Config 警告) ---
class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: int


class ChatResponse(BaseModel):
    response: str
    message_id: int


class NewSessionRequest(BaseModel):
    user_id: int


class NewSessionResponse(BaseModel):
    session_id: str
    welcome_message: str
    welcome_message_id: int
    user_id: int


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime


class FeedbackRequest(BaseModel):
    message_id: int
    session_id: str
    user_id: int
    feedback: Optional[str]


class KnowledgeEntryCreate(BaseModel):
    title: str
    type: str
    content: Optional[str] = None
    file_path: Optional[str] = None


class KnowledgeEntryUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None


class KnowledgeEntryResponse(BaseModel):
    id: int
    title: str
    type: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    source: str
    status: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    processing_notes: Optional[str] = None

    # 修复：使用 ConfigDict
    model_config = ConfigDict(from_attributes=True)


class PaginatedKnowledgeResponse(BaseModel):
    data: List[KnowledgeEntryResponse]
    total: int


class OverviewMetricsResponse(BaseModel):
    totalQuestions: int
    uniqueUsers: int
    unresolvedQuestions: int
    avgQuestionsPerSession: float


class QuestionTrendData(BaseModel):
    dates: List[str]
    data: List[int]


class PopularQuestionsData(BaseModel):
    names: List[str]
    values: List[int]


class ChartDataResponse(BaseModel):
    questionTrend: QuestionTrendData
    popularQuestions: PopularQuestionsData


class QaRecordResponse(BaseModel):
    id: int
    sessionId: str
    userId: int
    userQuestion: str
    userQuestionSummary: str
    aiAnswer: Optional[str] = None
    aiAnswerSummary: Optional[str] = None
    timestamp: datetime
    status: str
    feedback: Optional[str] = None
    adminNotes: Optional[str] = None
    knowledgeBaseContext: Optional[List[str]] = None

    # 修复：使用 ConfigDict 并配置 json_encoders
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class QaRecordDetailResponse(BaseModel):
    id: int
    sessionId: str
    userId: int
    userQuestion: str
    aiAnswer: Optional[str] = None
    timestamp: datetime
    status: str
    feedback: Optional[str] = None
    adminNotes: Optional[str] = None
    knowledgeBaseContext: Optional[List[str]] = None

    # 修复：使用 ConfigDict 并配置 json_encoders
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class QaRecordUpdate(BaseModel):
    status: Optional[str] = None
    feedback: Optional[str] = None
    adminNotes: Optional[str] = None


class PaginatedQaRecordsResponse(BaseModel):
    total: int
    records: List[QaRecordResponse]


# --- 权限依赖函数 ---
def get_current_user_role(user_id: int = Query(..., description="User ID for authentication"),
                          db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.role_id == 0:
        return "super_admin"
    elif user.role_id == 1:
        return "admin"
    elif user.role_id == 2:
        return "user"
    else:
        print(f"警告: 用户 {user_id} 的 role_id ({user.role_id}) 未知。默认为普通用户。")
        return "user"


def require_admin_role(role: str = Depends(get_current_user_role)):
    if role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    return role


# --- API 端点 ---

@app.post("/new_session", response_model=NewSessionResponse)
async def new_session(request: NewSessionRequest, db: DBSession = Depends(get_db)):
    user_exists = db.query(User).filter(User.id == request.user_id).first()
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    new_session_id = str(uuid.uuid4())

    db_session = DBSessionModel(id=new_session_id, user_id=request.user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    welcome_message_content = """您好！我是协和小智，您的福建师范大学协和学院AI招生咨询顾问，很高兴为您服务！

您可以问我以下问题，例如：

* **本科招生**：比如“本科招生章程是什么？”或“本科有哪些专业？”
* **专升本招生**：比如“专升本的申请条件是什么？”
* **录取分数线**：比如“2024年本科录取分数线是多少？”或“往年录取分数线查询”
* **收费标准**：比如“学费标准是多少？”或“住宿费怎么收？”
* **其他相关问题**：比如“校园生活怎么样？”或“如何申请入学？”

请尽管提问，我将尽力为您提供准确的官方信息。"""

    welcome_msg_db = DBMessageModel(
        session_id=new_session_id,
        role="assistant",
        content=welcome_message_content
    )
    db.add(welcome_msg_db)
    db.commit()
    db.refresh(welcome_msg_db)

    print(f"New session created and saved to DB for user {request.user_id}: {new_session_id}")
    return NewSessionResponse(
        session_id=new_session_id,
        welcome_message=welcome_message_content,
        welcome_message_id=welcome_msg_db.id,
        user_id=request.user_id
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: DBSession = Depends(get_db)):
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="AI model not initialized. Please check backend logs.")

    db_session = db.query(DBSessionModel).filter(
        DBSessionModel.id == request.session_id,
        DBSessionModel.user_id == request.user_id
    ).first()

    if not db_session:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Session not found or does not belong to this user.")

    try:
        user_msg_db = DBMessageModel(session_id=request.session_id, role="user", content=request.message)
        db.add(user_msg_db)
        db.commit()
        db.refresh(user_msg_db)

        # 1. 识别意图 (基础分类)
        enrollment_type = classify_query_type(llm_instance, request.message)
        is_score_query = is_score_line_query(llm_instance, request.message)
        is_fee_query_result = is_fee_query(llm_instance, request.message)
        identified_department = identify_department_query(llm_instance, request.message)
        identified_major = None

        if not identified_department:
            identified_major = identify_major_query(llm_instance, request.message)

        print(
            f"(内部判断：用户问题招生类型为：{enrollment_type}, 分数线：{is_score_query}, 收费：{is_fee_query_result}, 系：{identified_department}, 专业：{identified_major})")

        dynamic_system_prompt_content = SYSTEM_PROMPT
        knowledge_chunks_to_inject = []

        # =================== 【新增】图谱增强查询逻辑开始 ===================
        # 这里我们集成 graph_service_simple 的查询
        graph_context = ""

        # 定义触发词，减少不必要的查询开销
        # 当问题涉及费用、分数、专业归属等结构化数据强相关的领域时，优先查图谱
        triggers = ["学费", "费用", "多少钱", "系", "学院", "分数", "属于", "专业", "课程"]

        # 简单的触发条件：关键词匹配 或 意图分类器认为是相关问题
        should_query_graph = any(trigger in request.message for trigger in
                                 triggers) or is_fee_query_result or is_score_query or identified_major or identified_department

        if should_query_graph:
            print(f">>> 检测到相关意图，正在查询知识图谱 (Neo4j)...")
            try:
                # 调用 graph_service_simple.py 中的查询函数
                # 注意：这是一个同步调用，可能会增加一点响应时间
                graph_result = query_graph(request.message)

                # 如果查到了非空结果
                if graph_result and len(graph_result) > 0:
                    print(f">>> 图谱查询命中，结果: {graph_result}")
                    # 将结构化数据格式化为自然语言提示
                    graph_context = f"\n\n【数据库精确记录（优先级最高）】\n系统已从知识图谱数据库中查询到以下精确数据，请直接根据此数据回答，尤其是数字和金额：\n{str(graph_result)}"
                else:
                    print(">>> 图谱查询未找到直接相关的结构化数据。")
            except Exception as e:
                print(f"!!! 图谱查询模块出错（已降级，不影响主流程）: {e}")
        # =================== 【新增】图谱增强查询逻辑结束 ===================

        # 2. 检索 SQL 知识库 (原有的 RAG 流程)
        if is_score_query:
            score_kb_entry = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.type == 'policy',
                KnowledgeEntry.title.like('%录取分数%'),
                KnowledgeEntry.status == 'processed',
                KnowledgeEntry.is_deleted == False
            ).first()
            if score_kb_entry and score_kb_entry.content:
                chunk = f"\n\n以下是福建师范大学协和学院录取分数详情：\n{score_kb_entry.content}"
                knowledge_chunks_to_inject.append(chunk)

        if is_fee_query_result:
            fee_kb_entry = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.type == 'policy',
                KnowledgeEntry.title.like('%收费标准%'),
                KnowledgeEntry.status == 'processed',
                KnowledgeEntry.is_deleted == False
            ).first()
            if fee_kb_entry and fee_kb_entry.content:
                chunk = f"\n\n以下是福建师范大学协和学院收费标准汇总表的内容：\n{fee_kb_entry.content}"
                knowledge_chunks_to_inject.append(chunk)

        if enrollment_type == "本科":
            undergrad_kb_entry = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.type == 'policy',
                KnowledgeEntry.title.like('%本科招生章程%'),
                KnowledgeEntry.status == 'processed',
                KnowledgeEntry.is_deleted == False
            ).first()
            if undergrad_kb_entry and undergrad_kb_entry.content:
                chunk = f"\n\n以下是福建师范大学协和学院本科招生章程的内容：\n{undergrad_kb_entry.content}"
                knowledge_chunks_to_inject.append(chunk)
        elif enrollment_type == "专升本":
            junior_kb_entry = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.type == 'policy',
                KnowledgeEntry.title.like('%专升本招生章程%'),
                KnowledgeEntry.status == 'processed',
                KnowledgeEntry.is_deleted == False
            ).first()
            if junior_kb_entry and junior_kb_entry.content:
                chunk = f"\n\n以下是福建师范大学协和学院专升本招生章程的内容：\n{junior_kb_entry.content}"
                knowledge_chunks_to_inject.append(chunk)

        general_knowledge_entries = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.type.in_(['major', 'campus', 'faq']),
            KnowledgeEntry.status == 'processed',
            KnowledgeEntry.is_deleted == False
        ).all()
        for entry in general_knowledge_entries:
            if entry.content:
                chunk = f"\n\n以下是福建师范大学协和学院的通用知识（{entry.title}）：\n{entry.content}"
                knowledge_chunks_to_inject.append(chunk)

        # 3. 拼接 Prompt
        for chunk in knowledge_chunks_to_inject:
            dynamic_system_prompt_content += chunk

        # 【新增】将图谱数据注入 Prompt
        if graph_context:
            dynamic_system_prompt_content += graph_context

        if identified_department:
            majors_in_department = KNOWN_DEPARTMENTS_MAJORS.get(identified_department, [])
            if majors_in_department:
                majors_list_str = "、".join(majors_in_department)
                dynamic_system_prompt_content += f"\n\n**重要提示：用户正在询问【{identified_department}】系。请严格从上述提供的所有知识中，查找并列出该系下的所有专业：{majors_list_str}。对于每个专业，提供简要的介绍（如培养目标、主要方向等）。不要提及其他系或与【{identified_department}】系无关的内容。如果知识中没有某个专业的详细信息，请注明。**"
            else:
                dynamic_system_prompt_content += f"\n\n**重要提示：用户正在询问【{identified_department}】系。虽然识别到该系，但其下属专业列表为空或未找到。请根据现有知识回答，或告知用户无法提供该系下属专业信息。**"
        elif identified_major:
            dynamic_system_prompt_content += f"\n\n**重要提示：用户正在询问【{identified_major}】专业。请严格从上述提供的所有知识中，只提取并回答关于【{identified_major}】专业的信息。不要提及其他专业或与【{identified_major}】无关的内容。如果上述知识中没有【{identified_major}】的详细信息，请礼貌地告知用户无法提供。**"
        else:
            dynamic_system_prompt_content += "\n\n请严格基于上述提供的知识库内容回答用户问题，不要编造或猜测。如果知识库中没有相关信息，请礼貌地告知用户无法提供。"

        db_messages = db.query(DBMessageModel).filter(DBMessageModel.session_id == request.session_id).order_by(
            DBMessageModel.timestamp).all()
        current_history: List[ChatMessage] = []
        for msg in db_messages:
            current_history.append(ChatMessage(role=msg.role, content=msg.content))

        messages_to_send = [ChatMessage(role="system", content=dynamic_system_prompt_content)]
        messages_to_send.extend(current_history)

        response_obj = llm_instance.generate([messages_to_send])
        ai_response_content = response_obj.generations[0][0].text

        # 记录本次回答引用了哪些知识（图谱 + 文档）
        context_refs = knowledge_chunks_to_inject
        if graph_context:
            context_refs.append(f"KnowledgeGraph: {str(graph_context)[:100]}...")  # 简单记录

        ai_msg_db = DBMessageModel(
            session_id=request.session_id,
            role="assistant",
            content=ai_response_content,
            context_references=context_refs
        )
        db.add(ai_msg_db)
        db.commit()
        db.refresh(ai_msg_db)

        return ChatResponse(response=ai_response_content, message_id=ai_msg_db.id)

    except Exception as e:
        print(f"Error in chat endpoint for session {request.session_id} (user {request.user_id}): {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get("/history/{session_id}", response_model=List[Dict[str, Union[str, int, None]]])
async def get_chat_history(session_id: str, user_id: int, db: DBSession = Depends(get_db)):
    db_session = db.query(DBSessionModel).filter(
        DBSessionModel.id == session_id,
        DBSessionModel.user_id == user_id
    ).first()

    if not db_session:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Session not found or does not belong to this user.")

    db_messages = db.query(DBMessageModel).filter(DBMessageModel.session_id == session_id).order_by(
        DBMessageModel.timestamp).all()

    formatted_history = []
    for msg in db_messages:
        sender = 'user' if msg.role == 'user' else 'ai'
        formatted_history.append({
            "id": msg.id,
            "sender": sender,
            "content": msg.content,
            "feedback": msg.feedback
        })
    return formatted_history


@app.get("/user_sessions/{user_id}", response_model=List[SessionInfo])
async def get_user_sessions(user_id: int, db: DBSession = Depends(get_db)):
    user_exists = db.query(User).filter(User.id == user_id).first()
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    sessions = db.query(DBSessionModel).filter(DBSessionModel.user_id == user_id).order_by(
        DBSessionModel.created_at.desc()).all()

    return [SessionInfo(session_id=s.id, created_at=s.created_at) for s in sessions]


@app.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_backend(session_id: str, user_id: int, db: DBSession = Depends(get_db)):
    db_session = db.query(DBSessionModel).filter(
        DBSessionModel.id == session_id,
        DBSessionModel.user_id == user_id
    ).first()

    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Session not found or does not belong to this user.")

    db.delete(db_session)
    db.commit()
    print(f"Session {session_id} and its messages deleted from DB for user {user_id}.")
    return


@app.post("/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback(request: FeedbackRequest, db: DBSession = Depends(get_db)):
    db_message = db.query(DBMessageModel) \
        .join(DBSessionModel, DBMessageModel.session_id == DBSessionModel.id) \
        .filter(
        DBMessageModel.id == request.message_id,
        DBMessageModel.session_id == request.session_id,
        DBSessionModel.user_id == request.user_id,
        DBMessageModel.role == 'assistant'
    ).first()

    if not db_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or access denied.")

    db_message.feedback = request.feedback
    db.commit()
    db.refresh(db_message)

    print(f"Feedback '{request.feedback}' submitted for message ID {request.message_id}.")
    return {"message": "Feedback submitted successfully."}


# --- 问答记录与分析 API 端点 ---
@app.get("/qa_analytics/overview", response_model=OverviewMetricsResponse)
async def get_qa_overview(
        start_date: Optional[date] = Query(None, description="Start date for overview data (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="End date for overview data (YYYY-MM-DD)"),
        admin_role: str = Depends(require_admin_role),
        db: DBSession = Depends(get_db)
):
    query = db.query(DBMessageModel).filter(DBMessageModel.role == 'user')

    if start_date:
        query = query.filter(DBMessageModel.timestamp >= start_date)
    if end_date:
        query = query.filter(DBMessageModel.timestamp < (end_date + timedelta(days=1)))

    total_questions = query.count()

    unique_users_query = db.query(distinct(DBSessionModel.user_id)).join(
        DBMessageModel, DBSessionModel.id == DBMessageModel.session_id
    ).filter(DBMessageModel.role == 'user')

    if start_date:
        unique_users_query = unique_users_query.filter(DBMessageModel.timestamp >= start_date)
    if end_date:
        unique_users_query = unique_users_query.filter(DBMessageModel.timestamp < (end_date + timedelta(days=1)))

    unique_users = unique_users_query.count()

    unresolved_questions = query.filter(
        DBMessageModel.status.in_(['unresolved', 'pending'])
    ).count()

    sessions_with_messages_query = db.query(DBSessionModel.id).join(
        DBMessageModel, DBSessionModel.id == DBMessageModel.session_id
    ).filter(DBMessageModel.role == 'user')

    if start_date:
        sessions_with_messages_query = sessions_with_messages_query.filter(DBMessageModel.timestamp >= start_date)
    if end_date:
        sessions_with_messages_query = sessions_with_messages_query.filter(
            DBMessageModel.timestamp < (end_date + timedelta(days=1)))

    total_sessions_in_range = sessions_with_messages_query.distinct().count()

    avg_questions_per_session = 0.0
    if total_sessions_in_range > 0:
        avg_questions_per_session = round(total_questions / total_sessions_in_range, 1)

    return OverviewMetricsResponse(
        totalQuestions=total_questions,
        uniqueUsers=unique_users,
        unresolvedQuestions=unresolved_questions,
        avgQuestionsPerSession=avg_questions_per_session
    )


@app.get("/qa_analytics/charts", response_model=ChartDataResponse)
async def get_qa_chart_data(
        start_date: Optional[date] = Query(None, description="Start date for chart data (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="End date for chart data (YYYY-MM-DD)"),
        admin_role: str = Depends(require_admin_role),
        db: DBSession = Depends(get_db)
):
    daily_counts_query = db.query(
        func.DATE(DBMessageModel.timestamp).label('date'),
        func.count(DBMessageModel.id).label('count')
    ).filter(DBMessageModel.role == 'user')

    if start_date:
        daily_counts_query = daily_counts_query.filter(DBMessageModel.timestamp >= start_date)
    if end_date:
        daily_counts_query = daily_counts_query.filter(DBMessageModel.timestamp < (end_date + timedelta(days=1)))

    daily_counts = daily_counts_query.group_by(func.DATE(DBMessageModel.timestamp)).order_by(
        func.DATE(DBMessageModel.timestamp)).all()

    dates = [str(dc.date) for dc in daily_counts]
    trend_data = [dc.count for dc in daily_counts]
    question_trend = QuestionTrendData(dates=dates, data=trend_data)

    popular_questions_raw_query = db.query(
        DBMessageModel.content,
        func.count(DBMessageModel.id).label('count')
    ).filter(DBMessageModel.role == 'user')

    if start_date:
        popular_questions_raw_query = popular_questions_raw_query.filter(DBMessageModel.timestamp >= start_date)
    if end_date:
        popular_questions_raw_query = popular_questions_raw_query.filter(
            DBMessageModel.timestamp < (end_date + timedelta(days=1)))

    popular_questions_raw = popular_questions_raw_query.group_by(DBMessageModel.content).order_by(
        func.count(DBMessageModel.id).desc()).limit(10).all()

    popular_names = [pq.content for pq in popular_questions_raw]
    popular_values = [pq.count for pq in popular_questions_raw]
    popular_questions = PopularQuestionsData(names=popular_names, values=popular_values)

    return ChartDataResponse(questionTrend=question_trend, popularQuestions=popular_questions)


@app.get("/qa_analytics/records", response_model=PaginatedQaRecordsResponse)
async def get_qa_records(
        skip: int = 0,
        limit: int = 10,
        keyword: Optional[str] = Query(None, description="Search keyword in user question or AI answer"),
        status: Optional[str] = Query(None, description="Filter by resolution status (resolved, unresolved, pending)"),
        feedback: Optional[str] = Query(None, description="Filter by AI feedback (satisfied, dissatisfied)"),
        record_start_date: Optional[date] = Query(None, description="Filter records from this date (YYYY-MM-DD)"),
        record_end_date: Optional[date] = Query(None, description="Filter records up to this date (YYYY-MM-DD)"),
        admin_role: str = Depends(require_admin_role),
        db: DBSession = Depends(get_db)
):
    AIMessage = aliased(DBMessageModel)
    next_ai_message_subquery = db.query(
        DBMessageModel.id.label('user_msg_id'),
        func.min(AIMessage.id).label('ai_msg_id')
    ).filter(
        DBMessageModel.session_id == AIMessage.session_id,
        DBMessageModel.role == 'user',
        AIMessage.role == 'assistant',
        AIMessage.timestamp >= DBMessageModel.timestamp
    ).group_by(DBMessageModel.id).subquery()
    query = db.query(
        DBMessageModel,
        AIMessage.id.label('ai_id'),
        AIMessage.content.label('ai_content'),
        AIMessage.feedback.label('ai_feedback'),
        AIMessage.context_references.label('ai_context_references')
    ).outerjoin(
        next_ai_message_subquery, DBMessageModel.id == next_ai_message_subquery.c.user_msg_id
    ).outerjoin(
        AIMessage, next_ai_message_subquery.c.ai_msg_id == AIMessage.id
    ).filter(DBMessageModel.role == 'user')

    if keyword:
        query = query.filter(
            (DBMessageModel.content.contains(keyword)) |
            (AIMessage.content.contains(keyword))
        )
    if status:
        query = query.filter(DBMessageModel.status == status)
    if feedback:
        query = query.filter(AIMessage.feedback == feedback)
    if record_start_date:
        query = query.filter(DBMessageModel.timestamp >= record_start_date)
    if record_end_date:
        query = query.filter(DBMessageModel.timestamp < (record_end_date + timedelta(days=1)))

    query = query.order_by(DBMessageModel.timestamp.desc())
    total_records = query.count()
    results = query.offset(skip).limit(limit).all()

    qa_records_list = []
    for user_msg, ai_id, ai_content, ai_feedback, ai_context_references in results:
        user_question_summary = user_msg.content[:50] + '...' if len(user_msg.content) > 50 else user_msg.content
        ai_answer_summary = ai_content[:50] + '...' if ai_content and len(ai_content) > 50 else (
            ai_content if ai_content else '无回答')
        qa_records_list.append(QaRecordResponse(
            id=user_msg.id,
            sessionId=user_msg.session_id,
            userId=user_msg.session.user_id,
            userQuestion=user_msg.content,
            userQuestionSummary=user_question_summary,
            aiAnswer=ai_content,
            aiAnswerSummary=ai_answer_summary,
            timestamp=user_msg.timestamp,
            status=user_msg.status,
            feedback=ai_feedback,
            adminNotes=user_msg.admin_notes,
            knowledgeBaseContext=ai_context_references if ai_context_references else []
        ))
    return PaginatedQaRecordsResponse(total=total_records, records=qa_records_list)


@app.get("/qa_analytics/records/{user_message_id}", response_model=QaRecordDetailResponse)
async def get_qa_record_detail(
        user_message_id: int,
        admin_role: str = Depends(require_admin_role),
        db: DBSession = Depends(get_db)
):
    user_msg = db.query(DBMessageModel).filter(
        DBMessageModel.id == user_message_id,
        DBMessageModel.role == 'user'
    ).first()
    if not user_msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User message not found.")
    ai_msg = db.query(DBMessageModel).filter(
        DBMessageModel.session_id == user_msg.session_id,
        DBMessageModel.role == 'assistant',
        DBMessageModel.timestamp >= user_msg.timestamp
    ).order_by(DBMessageModel.timestamp.asc()).first()
    return QaRecordDetailResponse(
        id=user_msg.id,
        sessionId=user_msg.session_id,
        userId=user_msg.session.user_id,
        userQuestion=user_msg.content,
        aiAnswer=ai_msg.content if ai_msg else None,
        timestamp=user_msg.timestamp,
        status=user_msg.status,
        feedback=ai_msg.feedback if ai_msg else None,
        adminNotes=user_msg.admin_notes,
        knowledgeBaseContext=ai_msg.context_references if ai_msg and ai_msg.context_references else []
    )


@app.put("/qa_analytics/records/{user_message_id}", status_code=status.HTTP_200_OK)
async def update_qa_record(
        user_message_id: int,
        update_data: QaRecordUpdate,
        admin_role: str = Depends(require_admin_role),
        db: DBSession = Depends(get_db)
):
    user_msg = db.query(DBMessageModel).filter(
        DBMessageModel.id == user_message_id,
        DBMessageModel.role == 'user'
    ).first()
    if not user_msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User message not found.")
    if update_data.status is not None:
        user_msg.status = update_data.status
    if update_data.adminNotes is not None:
        user_msg.admin_notes = update_data.adminNotes
    if update_data.feedback is not None:
        ai_msg = db.query(DBMessageModel).filter(
            DBMessageModel.session_id == user_msg.session_id,
            DBMessageModel.role == 'assistant',
            DBMessageModel.timestamp > user_msg.timestamp
        ).order_by(DBMessageModel.timestamp.asc()).first()
        if ai_msg:
            ai_msg.feedback = update_data.feedback
            db.add(ai_msg)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    if update_data.feedback is not None and ai_msg:
        db.refresh(ai_msg)
    return {"message": "问答记录更新成功"}


@app.delete("/qa_analytics/records/{user_message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qa_record(
        user_message_id: int,
        admin_role: str = Depends(require_admin_role),
        db: DBSession = Depends(get_db)
):
    user_msg = db.query(DBMessageModel).filter(
        DBMessageModel.id == user_message_id,
        DBMessageModel.role == 'user'
    ).first()
    if not user_msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User message not found.")
    ai_msg = db.query(DBMessageModel).filter(
        DBMessageModel.session_id == user_msg.session_id,
        DBMessageModel.role == 'assistant',
        DBMessageModel.timestamp > user_msg.timestamp
    ).order_by(DBMessageModel.timestamp.asc()).first()
    db.delete(user_msg)
    if ai_msg:
        db.delete(ai_msg)
    db.commit()
    return


# --- 知识库管理 API 端点 ---

@app.post("/knowledge/upload_file", response_model=Dict[str, str])
async def upload_knowledge_file(
        file: UploadFile = File(...),
        user_id: int = Query(..., description="User ID for authentication"),
        admin_role: str = Depends(require_admin_role)
):
    try:
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_location = UPLOAD_FOLDER / unique_filename
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        return {"file_path": str(file_location.relative_to(BASE_DIR))}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件上传失败: {e}")


@app.post("/knowledge", response_model=KnowledgeEntryResponse)
async def create_knowledge_entry(
        knowledge_data: KnowledgeEntryCreate,
        background_tasks: BackgroundTasks,
        db: DBSession = Depends(get_db),
        admin_role: str = Depends(require_admin_role)
):
    if not knowledge_data.content and not knowledge_data.file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="知识内容或文件路径至少需要提供一个。")
    source_type = "手动录入"
    if knowledge_data.file_path:
        source_type = "文件上传"
    db_entry = KnowledgeEntry(
        title=knowledge_data.title,
        type=knowledge_data.type,
        content=knowledge_data.content,
        file_path=knowledge_data.file_path,
        source=source_type,
        status="pending",
        processing_notes="等待处理"
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    background_tasks.add_task(process_knowledge_entry, db_entry.id, db)
    return db_entry


@app.get("/knowledge", response_model=PaginatedKnowledgeResponse)
async def get_knowledge_entries(
        skip: int = 0,
        limit: int = 10,
        search_keyword: Optional[str] = None,
        knowledge_type: Optional[str] = None,
        knowledge_status: Optional[str] = None,
        db: DBSession = Depends(get_db),
        admin_role: str = Depends(require_admin_role)
):
    query = db.query(KnowledgeEntry).filter(KnowledgeEntry.is_deleted == False)

    if search_keyword:
        query = query.filter(
            (KnowledgeEntry.title.contains(search_keyword)) |
            (KnowledgeEntry.content.contains(search_keyword))
        )
    if knowledge_type:
        query = query.filter(KnowledgeEntry.type == knowledge_type)
    if knowledge_status:
        query = query.filter(KnowledgeEntry.status == knowledge_status)

    total_count = query.count()
    knowledge_entries = query.order_by(KnowledgeEntry.updated_at.desc()).offset(skip).limit(limit).all()

    return {"data": knowledge_entries, "total": total_count}


@app.get("/knowledge/{knowledge_id}", response_model=KnowledgeEntryResponse)
async def get_knowledge_entry(
        knowledge_id: int,
        db: DBSession = Depends(get_db),
        admin_role: str = Depends(require_admin_role)
):
    entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == knowledge_id,
                                            KnowledgeEntry.is_deleted == False).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge entry not found.")
    return entry


@app.put("/knowledge/{knowledge_id}", response_model=KnowledgeEntryResponse)
async def update_knowledge_entry(
        knowledge_id: int,
        knowledge_data: KnowledgeEntryUpdate,
        background_tasks: BackgroundTasks,
        db: DBSession = Depends(get_db),
        admin_role: str = Depends(require_admin_role)
):
    db_entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == knowledge_id,
                                               KnowledgeEntry.is_deleted == False).first()
    if not db_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge entry not found.")

    update_data = knowledge_data.model_dump(exclude_unset=True)

    if 'content' in update_data:
        db_entry.content = update_data['content']
        db_entry.status = "pending"
        db_entry.source = '手动录入'
        db_entry.file_path = None
        db_entry.processing_notes = "等待处理"

    if 'file_path' in update_data and update_data['file_path'] is not None:
        db_entry.file_path = update_data['file_path']
        db_entry.content = None
        db_entry.status = "pending"
        db_entry.source = '文件上传'
        db_entry.processing_notes = "等待处理"
    elif 'file_path' in update_data and update_data['file_path'] is None and db_entry.file_path:
        try:
            old_file_path = BASE_DIR / db_entry.file_path
            if old_file_path.exists():
                os.remove(old_file_path)
                print(f"旧文件 {old_file_path} 已删除。")
        except Exception as e:
            print(f"删除旧文件 {old_file_path} 时发生错误: {e}")
        db_entry.file_path = None
        db_entry.status = "pending"
        db_entry.processing_notes = "等待处理"

    for key, value in update_data.items():
        if key not in ['content', 'file_path']:
            setattr(db_entry, key, value)

    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    background_tasks.add_task(process_knowledge_entry, db_entry.id, db)
    return db_entry


@app.delete("/knowledge/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_entry(
        knowledge_id: int,
        db: DBSession = Depends(get_db),
        admin_role: str = Depends(require_admin_role)
):
    db_entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == knowledge_id,
                                               KnowledgeEntry.is_deleted == False).first()
    if not db_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge entry not found.")
    db_entry.is_deleted = True
    db.add(db_entry)
    db.commit()
    print(f"知识条目 {knowledge_id} 软删除成功。")
    return


@app.post("/knowledge/rebuild_index", status_code=status.HTTP_202_ACCEPTED)
async def rebuild_knowledge_index(
        background_tasks: BackgroundTasks,
        db: DBSession = Depends(get_db),
        admin_role: str = Depends(require_admin_role)
):
    entries_to_reprocess = db.query(KnowledgeEntry).filter(
        KnowledgeEntry.is_deleted == False,
        KnowledgeEntry.status.in_(['processed', 'failed'])
    ).all()
    for entry in entries_to_reprocess:
        entry.status = "pending"
        entry.processing_notes = "等待重新处理"
        db.add(entry)
    db.commit()
    for entry in entries_to_reprocess:
        background_tasks.add_task(process_knowledge_entry, entry.id, db)
    print(f"已触发 {len(entries_to_reprocess)} 个知识条目的重建索引任务。")
    return {"message": f"已成功触发 {len(entries_to_reprocess)} 个知识条目的重建索引任务。请稍后刷新列表查看状态。"}


# --- LLM意图分类函数 ---
def classify_query_type(llm: ChatSparkLLM, user_query: str) -> str:
    classification_prompt = ChatMessage(
        role="system",
        content="请判断以下用户问题主要涉及福建师范大学协和学院的本科招生信息还是专升本招生信息？请严格按照以下格式回答：`类型：[本科/专升本/通用]`。如果问题不明确或不属于这两类，请回答`类型：通用`。\n\n用户问题：" + user_query
    )
    try:
        response = llm.generate([[classification_prompt, ChatMessage(role="user", content=user_query)]])
        classification_text = response.generations[0][0].text
        if "类型：本科" in classification_text:
            return "本科"
        elif "类型：专升本" in classification_text:
            return "专升本"
        else:
            return "通用"
    except Exception as e:
        print(f"分类用户问题时发生错误: {e}")
        return "通用"


def is_score_line_query(llm: ChatSparkLLM, user_query: str) -> bool:
    score_line_prompt = ChatMessage(
        role="system",
        content="请判断以下用户问题是否与福建师范大学协和学院的录取分数线、录取分数、分数、最低分数、往年分数、投档线、录取分数详情等相关？请严格按照以下格式回答：`是否分数线：[是/否]`。\n\n用户问题：" + user_query
    )
    try:
        response = llm.generate([[score_line_prompt, ChatMessage(role="user", content=user_query)]])
        classification_text = response.generations[0][0].text
        print(f"(内部判断：分数线问题分类结果原始文本：{classification_text})")
        return "是否分数线：是" in classification_text
    except Exception as e:
        print(f"判断分数线问题时发生错误: {e}")
        return False


def is_fee_query(llm: ChatSparkLLM, user_query: str) -> bool:
    fee_prompt = ChatMessage(
        role="system",
        content="请判断以下用户问题是否与福建师范大学协和学院的收费标准、学费、住宿费、费用、缴费、收费、学年收费等相关？请严格按照以下格式回答：`是否收费：[是/否]`。\n\n用户问题：" + user_query
    )
    try:
        response = llm.generate([[fee_prompt, ChatMessage(role="user", content=user_query)]])
        classification_text = response.generations[0][0].text
        print(f"(内部判断：收费问题分类结果原始文本：{classification_text})")
        return "是否收费：是" in classification_text
    except Exception as e:
        print(f"判断收费问题时发生错误: {e}")
        return False


def identify_major_query(llm: ChatSparkLLM, user_query: str) -> Optional[str]:
    if not KNOWN_MAJORS:
        print("警告：KNOWN_MAJORS 列表为空，无法进行专业识别。请在 app.py 中配置 KNOWN_MAJORS。")
        return None
    major_list_str = "、".join(KNOWN_MAJORS)
    major_identification_prompt_content = f"""请判断以下用户问题是否涉及福建师范大学协和学院的某个具体专业。
如果涉及，请从以下列表中选择**唯一最匹配的专业名称**并严格按照格式回答：`专业：[专业名称]`。**请只输出一个专业名称，不要输出多个。**
如果问题不涉及具体专业，或无法判断，请回答`专业：无`。

已知专业列表：{major_list_str}

用户问题：{user_query}
"""
    major_identification_prompt = ChatMessage(
        role="system",
        content=major_identification_prompt_content
    )
    try:
        response = llm.generate([[major_identification_prompt, ChatMessage(role="user", content=user_query)]])
        classification_text = response.generations[0][0].text
        print(f"(内部判断：专业识别结果原始文本：{classification_text})")

        if classification_text.startswith("专业：") and "专业：无" not in classification_text:
            raw_identified_text = classification_text.replace("专业：", "").strip()
            temp_text = raw_identified_text.replace('，', ',').replace('、', ',')
            possible_majors_candidates = [m.strip() for m in temp_text.split(',') if m.strip()]
            for major_candidate in possible_majors_candidates:
                if major_candidate in KNOWN_MAJORS:
                    return major_candidate
            print(f"警告：LLM识别出专业 '{raw_identified_text}'，但其中没有单个名称在 KNOWN_MAJORS 列表中。")
            return None
        else:
            return None
    except Exception as e:
        print(f"识别专业问题时发生错误: {e}")
        return None


def identify_department_query(llm: ChatSparkLLM, user_query: str) -> Optional[str]:
    all_departments = list(KNOWN_DEPARTMENTS_MAJORS.keys())
    if not all_departments:
        print("警告：KNOWN_DEPARTMENTS_MAJORS 列表为空，无法进行系识别。")
        return None

    department_list_str = "、".join(all_departments)
    department_identification_prompt_content = f"""请判断以下用户问题是否涉及福建师范大学协和学院的某个具体的系。
如果涉及，请从以下列表中选择**唯一最匹配的系名称**并严格按照格式回答：`系：[系名称]`。**请只输出一个系名称，不要输出多个。**
如果问题不涉及具体系，或无法判断，请回答`系：无`。

已知系列表：{department_list_str}

用户问题：{user_query}
"""
    department_identification_prompt = ChatMessage(
        role="system",
        content=department_identification_prompt_content
    )
    try:
        response = llm.generate([[department_identification_prompt, ChatMessage(role="user", content=user_query)]])
        classification_text = response.generations[0][0].text
        print(f"(内部判断：系识别结果原始文本：{classification_text})")

        if classification_text.startswith("系：") and "系：无" not in classification_text:
            raw_identified_text = classification_text.replace("系：", "").strip()
            temp_text = raw_identified_text.replace('，', ',').replace('、', ',')
            possible_departments_candidates = [d.strip() for d in temp_text.split(',') if d.strip()]
            for dept_candidate in possible_departments_candidates:
                if dept_candidate in all_departments:
                    return dept_candidate
            print(f"警告：LLM识别出系 '{raw_identified_text}'，但其中没有单个名称在已知系列表中。")
            return None
        else:
            return None
    except Exception as e:
        print(f"识别系问题时发生错误: {e}")
        return None


# 提供静态文件服务
app.mount("/static", StaticFiles(directory=UPLOAD_FOLDER), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)