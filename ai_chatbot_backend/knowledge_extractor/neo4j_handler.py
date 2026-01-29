# knowledge_extractor/neo4j_handler.py

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import json  # 用于打印Cypher和参数

from .config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, SCHEMA_MERGE_RULES

_driver = None


def get_neo4j_driver():
    """获取Neo4j驱动实例，如果不存在则初始化"""
    global _driver
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            _driver.verify_connectivity()
            print("Neo4j driver initialized and connected.")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            _driver = None  # 确保连接失败时驱动为None
    return _driver


def close_neo4j_driver():
    """关闭Neo4j驱动"""
    global _driver
    if _driver:
        _driver.close()
        _driver = None
        print("Neo4j driver closed.")


def generate_cypher_for_entity(entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """根据实体信息生成Cypher MERGE语句和参数"""
    label = entity["label"]
    name = entity["text"]

    if label == "YEAR":
        try:
            name = int(name)  # 年份需要是整数
        except ValueError:
            return None  # 非法年份，跳过

    merge_rule = SCHEMA_MERGE_RULES.get(label)
    if merge_rule:
        params = {"name": name}
        # 如果需要设置其他默认属性，可以在这里添加
        if label == "COLLEGE":
            # 示例：这些属性可能需要从更全局的配置或默认值中获取
            params.update({
                "full_name": "福建师范大学协和学院",
                "address": "福州市闽侯上街大学城学府南路68号",
                "website": "http://cuc.fjnu.edu.cn/",
                "admissions_phone": "0591-22868770",
                "description": "福建师范大学协和学院是经福建省人民政府批准设立并通过教育部确认的独立学院。"
            })
        elif label == "MAJOR":
            params.update({
                "full_name": name,  # 默认full_name和name相同
                "type": "普通专业"
            })

        return {"query": merge_rule, "params": params}
    return None


def generate_cypher_for_relation(relation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """根据关系信息生成Cypher MERGE语句和参数"""
    source_label = relation["source"]["label"]
    source_name = relation["source"]["text"]
    rel_type = relation["type"]

    params = {"source_name": source_name}  # 所有关系都有源实体名称参数

    if rel_type == "OFFERS_MAJOR":
        target_label = relation["target"]["label"]
        target_name = relation["target"]["text"]
        params["target_name"] = target_name
        query = f"""
        MATCH (s:{source_label} {{name: $source_name}})
        MATCH (t:{target_label} {{name: $target_name}})
        MERGE (s)-[:{rel_type}]->(t)
        """
        return {"query": query, "params": params}

    elif rel_type == "HAS_FEE_STANDARD_FOR_YEAR":
        major_name = relation["source"]["text"]
        year_val = relation["target_id_info"]["year"]
        amount = relation["target_id_info"]["amount"]
        fee_standard_id = relation["target_id_info"]["fee_standard_id"]
        fee_item_name = "学费"  # 假设这里只处理学费

        params.update({
            "major_name": major_name,
            "year_val": year_val,
            "amount": amount,
            "fee_item_name": fee_item_name,
            "fee_standard_id": fee_standard_id
        })
        query = f"""
        MATCH (m:Major {{name: $major_name}})
        MATCH (fi:FeeItem {{name: $fee_item_name}})
        MERGE (y:Year {{value: $year_val}})
        MERGE (fs:FeeStandard {{id: $fee_standard_id}})
        ON CREATE SET fs.amount = $amount, fs.unit = "元/生.学年"
        ON MATCH SET fs.amount = $amount, fs.unit = "元/生.学年"
        MERGE (m)-[:HAS_FEE_STANDARD_FOR_YEAR {{year: $year_val}}]->(fs)
        MERGE (fs)-[:HAS_FEE_ITEM]->(fi)
        """
        return {"query": query, "params": params}

    elif rel_type == "REFERENCES_DOCUMENT":
        # 关联 FeeItem 或 Policy 到 PolicyDocument
        # 简化：假设这里是 FeeItem 关联 PolicyDocument
        target_name = relation["target"]["text"]  # policy_doc_id
        params["target_name"] = target_name
        query = f"""
        MATCH (s:{source_label} {{name: $source_name}})
        MATCH (t:PolicyDocument {{doc_id: $target_name}})
        MERGE (s)-[:{rel_type}]->(t)
        """
        return {"query": query, "params": params}

    elif rel_type in ["DEVELOPS_COMPETENCY", "COVERS_COURSE", "LEADS_TO_CAREER", "HAS_FACILITY", "HAS_COOPERATION_WITH",
                      "UTILIZES_RESOURCE_FROM", "HAS_DORM_TYPE", "HAS_CANTEEN", "HAS_STUDENT_ORGANIZATION"]:
        target_label = relation["target"]["label"]
        target_name = relation["target"]["text"]
        params["target_name"] = target_name
        query = f"""
        MATCH (s:{source_label} {{name: $source_name}})
        MATCH (t:{target_label} {{name: $target_name}})
        MERGE (s)-[:{rel_type}]->(t)
        """
        return {"query": query, "params": params}

    # 其他关系类型可以根据 Schema 扩展

    return None


def import_extracted_data_to_neo4j(extracted_data: Dict[str, List[Dict[str, Any]]], batch_size: int = 50):
    """
    将抽取到的实体和关系数据导入Neo4j。
    使用事务分批提交以提高效率。
    """
    driver = get_neo4j_driver()
    if not driver:
        print("Neo4j driver not available. Data import skipped.")
        return

    all_cypher_ops = []  # 存储所有待执行的Cypher查询和参数

    # 1. 生成实体创建的Cypher
    for entity in extracted_data["entities"]:
        cypher_op = generate_cypher_for_entity(entity)
        if cypher_op:
            all_cypher_ops.append(cypher_op)

    # 2. 生成关系创建的Cypher
    for relation in extracted_data["relations"]:
        cypher_op = generate_cypher_for_relation(relation)
        if cypher_op:
            all_cypher_ops.append(cypher_op)

    print(f"Generated {len(all_cypher_ops)} Cypher operations.")

    # 3. 分批执行
    with driver.session() as session:
        for i in range(0, len(all_cypher_ops), batch_size):
            batch_ops = all_cypher_ops[i:i + batch_size]

            try:
                with session.begin_transaction() as tx:
                    for op in batch_ops:
                        tx.run(op["query"], op["params"])
                print(f"Batch {i // batch_size + 1}/{len(all_cypher_ops) // batch_size + 1} committed successfully.")
            except Exception as e:
                print(f"Error committing batch {i // batch_size + 1}. Error: {e}")
                # 可以在这里添加更详细的日志记录，如具体的失败查询
                for op in batch_ops:
                    print(f"  Failed Query: {op['query']}")
                    print(f"  Failed Params: {json.dumps(op['params'], ensure_ascii=False)}")
                # 出现错误回滚整个批次，并停止后续导入
                raise

    print("数据导入Neo4j完成。")