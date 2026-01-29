import os
import sys
from pathlib import Path  # <--- ✅ 这里必须导入 Path
from knowledge_extractor.text_processor import get_text_from_file
from knowledge_extractor.ner_re_pipeline import extract_entities, extract_relations
from knowledge_extractor.text_processor import load_spacy_model

# 👇 请修改为你本地真实的文件路径
TEST_FILE_STR = "本地知识库/《福建师范大学协和学院2024 - 2025学年收费标准汇总表》.docx"


def test_extraction():
    # ✅ 强制转换为 Path 对象，防止报错
    file_path = Path(TEST_FILE_STR)

    if not file_path.exists():
        print(f"❌ 错误：找不到文件: {file_path.absolute()}")
        print("请检查文件名是否正确！")
        return

    print(f"--- 正在测试文件： {file_path.name} ---")

    # 1. 读取文本
    text = get_text_from_file(file_path)
    if not text:
        print("❌ 读取失败：文本为空。")
        return

    print(f"提取文本长度： {len(text)}")

    # 2. 抽取实体
    print("\n--- 正在抽取实体 ---")
    entities = extract_entities(text)
    print(f"发现实体总数: {len(entities)}")

    # 打印前几个看看
    depts = [e['text'] for e in entities if e['label'] == 'DEPARTMENT']
    majors = [e['text'] for e in entities if e['label'] == 'MAJOR']
    money = [e['text'] for e in entities if e['label'] == 'MONEY_AMOUNT']

    print(f"发现系别 ({len(depts)}): {depts[:3]}...")
    print(f"发现专业 ({len(majors)}): {majors[:3]}...")
    print(f"发现金额 ({len(money)}): {money[:3]}...")

    # 3. 抽取关系
    print("\n--- 正在抽取关系 ---")
    nlp = load_spacy_model()
    doc = nlp(text)
    relations = extract_relations(doc, entities)

    print(f"发现关系总数: {len(relations)}")

    offer_rels = [r for r in relations if r['type'] == 'OFFERS_MAJOR']
    fee_rels = [r for r in relations if r['type'] == 'HAS_FEE_STANDARD_FOR_YEAR']

    print(f"👉 系->专业 关系数: {len(offer_rels)}")
    print(f"👉 专业->学费 关系数: {len(fee_rels)}")

    if len(offer_rels) > 0 and len(fee_rels) > 0:
        print("\n✅✅✅ 测试通过！代码逻辑完美！ ✅✅✅")
        print("示例数据：")
        print(f"  {offer_rels[0]['source']['text']} --开设--> {offer_rels[0]['target']['text']}")
        print(f"  {fee_rels[0]['source']['text']} --学费--> {fee_rels[0]['target_id_info']['amount']}")
    else:
        print("\n❌ 警告：关系不全。请检查是否有系别和金额实体。")


if __name__ == "__main__":
    test_extraction()