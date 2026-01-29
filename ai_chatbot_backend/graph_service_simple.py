# graph_service_simple.py
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_community.chat_models import ChatSparkLLM
from langchain.prompts import PromptTemplate

# 加载环境变量
load_dotenv()

# ==========================================
# 1. 数据库连接配置 (手动模式，无需插件)
# ==========================================
URI = os.getenv('NEO4J_URI')
USERNAME = os.getenv('NEO4J_USERNAME')
PASSWORD = os.getenv('NEO4J_PASSWORD')

if not all([URI, USERNAME, PASSWORD]):
    raise ValueError("请检查 .env 文件，确保 NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD 都已设置！")


def run_cypher(query: str):
    """原生 Neo4j 驱动执行器"""
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    try:
        driver.verify_connectivity()
        records, summary, keys = driver.execute_query(query)
        # 转换为字典列表
        return [dict(record) for record in records]
    except Exception as e:
        print(f"执行 Cypher 报错: {e}")
        return None
    finally:
        driver.close()


# ==========================================
# 2. 手动 Schema (核心地图)
# ==========================================
MANUAL_SCHEMA = """
节点类型:
- Major (属性: name, full_name, type)
- Department (属性: name)
- FeeStandard (属性: amount, unit, id)
- FeeItem (属性: name)
- Year (属性: value)

关系类型:
- (:Major)-[:OFFERS_MAJOR]->(:Department)
- (:Major)-[:HAS_FEE_STANDARD_FOR_YEAR {year: int}]->(:FeeStandard)
- (:FeeStandard)-[:HAS_FEE_ITEM]->(:FeeItem)
"""

# ==========================================
# 3. 配置 LLM
# ==========================================
# 升级 langchain-community 后，这里可以直接传参数，不会报错了
llm = ChatSparkLLM(
    spark_app_id=os.getenv('SPARKAI_APP_ID'),
    spark_api_key=os.getenv('SPARKAI_API_KEY'),
    spark_api_secret=os.getenv('SPARKAI_API_SECRET'),
    spark_api_url='wss://spark-api.xf-yun.com/v4.0/chat',
    spark_llm_domain='4.0Ultra',
    temperature=0.1,  # 直接写，没问题
    top_k=4
)

PROMPT_TEMPLATE = """
你是一个 Neo4j 专家。请根据 Schema 编写 Cypher 查询。

【Schema】
{schema}

【规则】
1. 查找学费路径: (Major)-[:HAS_FEE_STANDARD_FOR_YEAR]->(FeeStandard)-[:HAS_FEE_ITEM]->(FeeItem {{name: '学费'}})
2. 专业名模糊匹配: m.name CONTAINS 'xx'
3. 只返回属性值(amount, name)，不要返回节点。
4. 直接输出 Cypher 语句，不要包含 Markdown 格式。

【用户问题】: {question}

【Cypher语句】:
"""

prompt = PromptTemplate(input_variables=["schema", "question"], template=PROMPT_TEMPLATE)


# ==========================================
# 4. 问答主逻辑
# ==========================================
def query_graph(user_query: str):
    try:
        # 第一步：LLM 生成 Cypher
        full_prompt = prompt.format(schema=MANUAL_SCHEMA, question=user_query)
        response = llm.invoke(full_prompt)  # 最新版推荐用 invoke
        cypher_query = response.content.strip()

        # 清洗结果
        cypher_query = cypher_query.replace("```cypher", "").replace("```", "")
        print(f"\n[AI生成的Cypher]: {cypher_query}")

        # 第二步：执行 Cypher
        result = run_cypher(cypher_query)
        return result

    except Exception as e:
        print(f"流程出错: {e}")
        return None


# ==========================================
# 5. 测试运行
# ==========================================
if __name__ == "__main__":
    print(">>> 开始测试...")
    q = "通信工程学费是多少？"
    print(f"\n>>> 提问: {q}")

    # 运行查询
    answer = query_graph(q)
    print(f"\n>>> 最终答案: {answer}")