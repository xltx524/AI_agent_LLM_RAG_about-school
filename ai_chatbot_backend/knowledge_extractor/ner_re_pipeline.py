# knowledge_extractor/ner_re_pipeline.py

import re
import spacy
from spacy.matcher import PhraseMatcher, Matcher
from typing import List, Dict, Any

from .config import ENTITY_DICTIONARIES, REGEX_PATTERNS, RELATION_KEYWORDS
from .text_processor import load_spacy_model

_nlp = None
_phrase_matcher = None
_regex_matcher = None


def init_ner_re_components():
    global _nlp, _phrase_matcher, _regex_matcher
    if _nlp is None:
        _nlp = load_spacy_model()

        # 1. 词典匹配
        _phrase_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
        for label, terms in ENTITY_DICTIONARIES.items():
            patterns = [_nlp.make_doc(str(t)) for t in terms]
            _phrase_matcher.add(label, patterns)

        # 2. 正则匹配
        _regex_matcher = Matcher(_nlp.vocab)
        for label, regex in REGEX_PATTERNS.items():
            _regex_matcher.add(label, [[{"TEXT": {"REGEX": regex}}]])


def extract_entities(text: str) -> List[Dict[str, Any]]:
    if _nlp is None: init_ner_re_components()
    doc = _nlp(text)
    entities = []

    # PhraseMatcher
    for match_id, start, end in _phrase_matcher(doc):
        span = doc[start:end]
        entities.append(
            {"text": span.text, "label": _nlp.vocab.strings[match_id], "start": span.start_char, "end": span.end_char})

    # RegexMatcher
    for match_id, start, end in _regex_matcher(doc):
        span = doc[start:end]
        label = _nlp.vocab.strings[match_id]
        text_val = span.text.replace("元", "") if label == "MONEY_AMOUNT" else span.text
        entities.append({"text": text_val, "label": label, "start": span.start_char, "end": span.end_char})

    # 去重
    unique_ents = []
    seen = set()
    for ent in sorted(entities, key=lambda x: (x['start'], -len(x['text']))):
        key = (ent['start'], ent['end'], ent['label'])
        if key not in seen:
            unique_ents.append(ent)
            seen.add(key)

    # 按在文中出现的顺序排序，这对于处理“上下文”非常重要
    unique_ents.sort(key=lambda x: x['start'])
    return unique_ents


def extract_relations(doc: spacy.tokens.Doc, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    relations = []

    # --- 关键逻辑：上下文记忆 ---
    # 用来解决表格合并单元格的问题：如果前面提到了"信息技术系"，后面紧跟的专业都默认属于它
    current_department = None

    # 辅助：按顺序遍历实体
    for i, ent in enumerate(entities):

        # 1. 更新当前上下文的系别
        if ent['label'] == 'DEPARTMENT':
            current_department = ent

        # 2. 系 -> 专业 (OFFERS_MAJOR)
        # 逻辑：只要发现了专业，且之前出现过系别，就默认连上！
        # (这比之前的“同一行”逻辑更强大，能处理跨行/合并单元格)
        if ent['label'] == 'MAJOR':
            if current_department:
                # 建立关系
                relations.append({
                    "source": current_department,
                    "target": ent,
                    "type": "OFFERS_MAJOR"
                })

            # 3. 专业 -> 学费 (HAS_FEE_STANDARD_FOR_YEAR)
            # 逻辑：往后找最近的一个金额
            # 我们向后看最多3个实体，看有没有 MONEY_AMOUNT
            for j in range(1, 4):
                if i + j < len(entities):
                    next_ent = entities[i + j]

                    # 如果中间插了别的专业或系，停止查找，防止连错
                    if next_ent['label'] in ['MAJOR', 'DEPARTMENT']:
                        break

                    if next_ent['label'] == 'MONEY_AMOUNT':
                        try:
                            amount = int(next_ent['text'])
                            if amount > 5000:  # 简单的阈值，过滤掉小杂费
                                rel_id = f"学费-{ent['text']}-2024"
                                relations.append({
                                    "source": ent,
                                    "target_id_info": {
                                        "major_name": ent['text'],
                                        "year": 2024,
                                        "amount": amount,
                                        "fee_standard_id": rel_id
                                    },
                                    "type": "HAS_FEE_STANDARD_FOR_YEAR"
                                })
                                break  # 找到一个学费就够了
                        except:
                            pass

        # 4. 其他普通关系 (基于关键词)
        for j, target_ent in enumerate(entities):
            if i == j: continue

            # 这里简化逻辑，如果距离较近且有关键词，就建立关系
            # 计算距离 (简单的字符距离)
            dist = abs(ent['start'] - target_ent['start'])
            if dist > 100: continue  # 太远的不看

            # 获取中间文本
            s, e = sorted([ent['end'], target_ent['start']]) if ent['start'] < target_ent['start'] else sorted(
                [target_ent['end'], ent['start']])
            text_between = doc.text[s:e]

            if ent['label'] == 'MAJOR' and target_ent['label'] == 'COURSE':
                if any(k in text_between for k in RELATION_KEYWORDS['COVERS_COURSE']):
                    relations.append({"source": ent, "target": target_ent, "type": "COVERS_COURSE"})

    return relations