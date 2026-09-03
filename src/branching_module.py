# -*- coding: utf-8 -*-
"""
Модуль створення розгалужених тестів/сценаріїв (branching scenarios)
з усіма настройками. Містить вбудований системний промпт (за специфікацією:
SCENARIO_TITLE / LEARNING_OBJECTIVES / NODE_x / END_x / INSTRUCTOR_GUIDE /
MOODLE_GIFT_EXPORT, усе українською, три рівні складності, SCORE_CHANGE,
типи результатів SUCCESS/PARTIAL_SUCCESS/FAILURE/CRITICAL_FAILURE).
Також містить ПАРСЕР, що читає згенерований сценарій без розмітки і
будує ієрархічне дерево для відображення.
"""

import re
import json
import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# СИСТЕМНИЙ ПРОМПТ (вбудований, додається автоматично)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """ТИ — генератор розгалужених навчальних сценаріїв (branching scenarios)
у формі дерева рішень з системою балів та автоматичним експортом у GIFT
для Moodle.

ЖОРСТКЕ ПРАВИЛО МОВИ: увесь зміст сценарію (вузли, кінцівки, посібник для
викладача, GIFT) пиши УКРАЇНСЬКОЮ мовою, незалежно від мови вводу.

РІВНІ СКЛАДНОСТІ:
• easy  — 3–4 вузли, 2–3 варіанти, 2–3 кінцівки, SCORE_CHANGE −1..+2,
          переважно «знання/розуміння».
• medium— 4–6 вузлів, 3–4 варіанти, 3–4 кінцівки, SCORE_CHANGE −2..+2,
          «застосування/аналіз», можливі частково правильні варіанти.
• hard  — 6–8 вузлів, 3–5 варіантів, 4–5 кінцівок, SCORE_CHANGE −3..+3,
          ключові вузли (KEY_NODE), CRITICAL_ERROR, «аналіз/оцінка».

БЕЗПЕКА ТА ЕТИКА: не пропонуй небезпечних дій без явного маркування їх як
хибних з поясненням у фідбеці; у медичних/безпекових сценаріях не
нормалізуй небезпечні практики; небезпечні дії отримують від'ємні бали.

СТРУКТУРА ВИВОДУ (суворо, у цьому порядку, без зайвого тексту):

SCENARIO_TITLE: <назва українською>

LEARNING_OBJECTIVES:
LO1: ...
LO2: ...

NODE_1
SITUATION: <2–6 речень українською>
QUESTION: <одне чітке питання>
OPTION_A: <текст варіанта>
NEXT_NODE_A: NODE_2 | END_1
SCORE_CHANGE_A: +2
COMMENT_A: <коментар для викладача українською>
OPTION_B: ...
NEXT_NODE_B: ...
SCORE_CHANGE_B: -1
COMMENT_B: ...
(тощо для всіх варіантів A..E)

END_1
TITLE: <назва результату>
RESULT_TYPE: SUCCESS | PARTIAL_SUCCESS | FAILURE | CRITICAL_FAILURE
SUMMARY: <опис українською>
SCORE_RANGE: <наприклад, 5..6>
COMMENT: <коментар для викладача>

INSTRUCTOR_GUIDE:
MAP_OVERVIEW: ...
SCORING_RULES: ...
FEEDBACK_TEMPLATES: ...
LINK_TO_LEARNING_OBJECTIVES: ...

MOODLE_GIFT_EXPORT:
<послідовність GIFT-питань для кожного NODE_x: кожен вузол = одне питання
 multichoice; правильна відповідь = %100%, частково правильні = ~%50%,
 грубо хибні = ~%-25% тощо; для кожного варіанта короткий фідбек (#...);
 службові рядки-коментарі починай з «// » — вони не заважають імпорту:
   // NEXT_NODE_A = NODE_2; SCORE_CHANGE_A = +2
 Усе українською.>

Не додавай жодного тексту поза цією структурою.
"""


class BranchingError(Exception):
    pass


def build_user_prompt(topic, audience, difficulty_level, learning_objectives,
                      context_brief, style, scoring_model, constraints):
    lo = "\n".join(f"– {x}" for x in learning_objectives if x.strip())
    return f"""ПАРАМЕТРИ СЦЕНАРІЮ:
topic: {topic}
audience: {audience}
difficulty_level: {difficulty_level}
learning_objectives:
{lo}
context_brief: {context_brief}
style: {style}
scoring_model: {scoring_model}
constraints: {constraints}

Згенеруй повний розгалужений сценарій за наведеною структурою українською.
"""


def generate_branching(provider, api_key, model, topic, audience,
                       difficulty_level, learning_objectives, context_brief,
                       style, scoring_model, constraints, base_url="",
                       timeout=180):
    """Генерація розгалуженого сценарію через будь-який LLM-провайдер
    (універсальний виклик llm_module.chat — Gemini / OpenAI-сумісні /
    Anthropic)."""
    if not api_key.strip():
        raise BranchingError("Введіть API-ключ.")
    prompt = SYSTEM_PROMPT + "\n\n" + build_user_prompt(
        topic, audience, difficulty_level, learning_objectives,
        context_brief, style, scoring_model, constraints)
    try:
        from llm_module import chat
        return chat(provider, api_key, model, prompt, base_url=base_url,
                    max_tokens=8192, temperature=0.7, timeout=timeout)
    except Exception as e:
        raise BranchingError(str(e))


# ---------------------------------------------------------------------------
# ПАРСЕР: читання згенерованого сценарію БЕЗ розмітки у вигляд дерева
# ---------------------------------------------------------------------------
def parse_scenario(text: str) -> dict:
    """
    Parse the generated scenario (plain structure, no markup) into a
    hierarchical tree:
      {title, objectives[], nodes[{id, situation, question, options[]}],
       ends[{id, title, type, summary, range, comment}], guide{}}
    Each option: {label, text, next_node, score_change, comment}
    """
    tree = {"title": "", "objectives": [], "nodes": [], "ends": [],
            "guide": {}, "gift": ""}

    # GIFT section (kept raw)
    mg = re.search(r"MOODLE_GIFT_EXPORT\s*:?\s*\n(.*)", text, re.DOTALL)
    if mg:
        tree["gift"] = mg.group(1).strip()
        text = text[:mg.start()]

    m = re.search(r"SCENARIO_TITLE\s*:\s*(.+)", text)
    if m:
        tree["title"] = m.group(1).strip()

    lo = re.search(r"LEARNING_OBJECTIVES\s*:?\s*\n(.*?)(?=\n\s*NODE_|\Z)",
                   text, re.DOTALL)
    if lo:
        tree["objectives"] = [l.strip(" –-•") for l in lo.group(1).splitlines()
                              if re.match(r"\s*(LO\d|–|-|•)", l)]

    # nodes
    node_blocks = re.split(r"\n\s*(?=NODE_\d+)", text)
    for nb in node_blocks:
        nm = re.match(r"\s*NODE_(\d+)", nb)
        if not nm:
            continue
        node = {"id": f"NODE_{nm.group(1)}", "situation": "", "question": "",
                "options": []}
        sm = re.search(r"SITUATION\s*:\s*(.+?)(?=\n\s*QUESTION:)", nb, re.DOTALL)
        if sm:
            node["situation"] = " ".join(sm.group(1).split())
        qm = re.search(r"QUESTION\s*:\s*(.+)", nb)
        if qm:
            node["question"] = qm.group(1).strip()
        # options
        for om in re.finditer(
                r"OPTION_([A-E])\s*:\s*(.+?)(?=\n\s*NEXT_NODE_[A-E]:)", nb,
                re.DOTALL):
            lab = om.group(1)
            opt = {"label": lab, "text": " ".join(om.group(2).split()),
                   "next_node": "", "score_change": 0, "comment": ""}
            nn = re.search(rf"NEXT_NODE_{lab}\s*:\s*(\S+)", nb)
            sc = re.search(rf"SCORE_CHANGE_{lab}\s*:\s*([+-]?\d+)", nb)
            cm = re.search(rf"COMMENT_{lab}\s*:\s*(.+)", nb)
            if nn:
                opt["next_node"] = nn.group(1).strip()
            if sc:
                opt["score_change"] = int(sc.group(1))
            if cm:
                opt["comment"] = cm.group(1).strip()
            node["options"].append(opt)
        tree["nodes"].append(node)

    # ends
    for eb in re.finditer(r"\n\s*(END_\d+)\s*\n(.*?)(?=\n\s*END_\d+|\n\s*INSTRUCTOR_GUIDE|\Z)",
                          text, re.DOTALL):
        eid = eb.group(1)
        blk = eb.group(2)
        end = {"id": eid, "title": "", "type": "", "summary": "",
               "range": "", "comment": ""}
        for key, pat in [
                ("title", r"TITLE\s*:\s*(.+?)\s*(?=\n\s*RESULT_TYPE:|$)"),
                ("type", r"RESULT_TYPE\s*:\s*(\S+)"),
                ("summary", r"SUMMARY\s*:\s*(.+?)\s*(?=\n\s*SCORE_RANGE:|$)"),
                ("range", r"SCORE_RANGE\s*:\s*(.+?)\s*(?=\n\s*COMMENT:|$)"),
                ("comment", r"COMMENT\s*:\s*(.+?)\s*$")]:
            mm = re.search(pat, blk, re.DOTALL)
            if mm:
                end[key] = " ".join(mm.group(1).split())
        tree["ends"].append(end)

    # guide
    gm = re.search(r"INSTRUCTOR_GUIDE\s*:?\s*\n(.*?)(?=\Z)", text, re.DOTALL)
    if gm:
        g = gm.group(1)
        for key, pat in [("MAP_OVERVIEW", r"MAP_OVERVIEW\s*:\s*(.+?)(?=\n\s*SCORING_RULES:|\Z)"),
                         ("SCORING_RULES", r"SCORING_RULES\s*:\s*(.+?)(?=\n\s*FEEDBACK_TEMPLATES:|\Z)"),
                         ("FEEDBACK_TEMPLATES", r"FEEDBACK_TEMPLATES\s*:\s*(.+?)(?=\n\s*LINK_TO_LEARNING_OBJECTIVES:|\Z)"),
                         ("LINK_TO_LEARNING_OBJECTIVES", r"LINK_TO_LEARNING_OBJECTIVES\s*:\s*(.+)")]:
            mm = re.search(pat, g, re.DOTALL)
            if mm:
                tree["guide"][key] = " ".join(mm.group(1).split())
    return tree


def _node_numeric_id(node_id: str) -> int:
    """NODE_12 -> 12, END_3 -> 1000+3 (щоб не перетинатися з вузлами)."""
    m = re.match(r"NODE_(\d+)", node_id or "")
    if m:
        return int(m.group(1))
    m = re.match(r"END_(\d+)", node_id or "")
    if m:
        return 1000 + int(m.group(1))
    return 0


def tree_to_h5p(tree: dict) -> dict:
    """Конвертує розпарсений сценарій у JSON-структуру H5P Branching
    Scenario (content.json для H5P.BranchingScenario).

    Будує масиви content/params: кожен вузол = BranchingQuestion,
    кожна кінцівка = BranchingScenario End Screen.
    """
    import uuid
    params = []
    node_index = {}          # "NODE_1" -> index у params
    end_index = {}           # "END_1"  -> index у params

    # --- спершу всі вузли (BranchingQuestion) ---
    for node in tree.get("nodes", []):
        alts = []
        for opt in node.get("options", []):
            nxt = opt.get("next_node", "")
            fb = opt.get("comment", "")
            # nextContentId підставимо пізніше (після індексації всіх)
            alts.append({
                "nextContentId": nxt,          # тимчасово текст, потім int
                "feedback": {"subtitle": fb},
                "text": opt.get("text", ""),
            })
        params.append({
            "content": {
                "library": "H5P.BranchingQuestion 1.0",
                "params": {
                    "question": node.get("question") or node.get("situation", ""),
                    "alternatives": alts,
                },
                "subContentId": str(uuid.uuid4()),
                "metadata": {"contentType": "Branching Question",
                             "license": "U",
                             "title": node.get("id", "")},
            },
            "type": {"library": "H5P.BranchingQuestion 1.0",
                      "params": {}},
            "subContentId": str(uuid.uuid4()),
            "_node_id": node.get("id", ""),
            "_alts_next": alts,
        })
        node_index[node["id"]] = len(params) - 1

    # --- потім усі кінцівки (End Screen) ---
    for end in tree.get("ends", []):
        params.append({
            "content": {
                "library": "H5P.AdvancedText 1.1",
                "params": {"text":
                           f"<h3>{end.get('title','')}</h3>"
                           f"<p><b>{end.get('type','')}</b></p>"
                           f"<p>{end.get('summary','')}</p>"},
                "subContentId": str(uuid.uuid4()),
                "metadata": {"contentType": "Text", "license": "U",
                             "title": end.get("id", "")},
            },
            "type": {"library": "H5P.AdvancedText 1.1", "params": {}},
            "subContentId": str(uuid.uuid4()),
            "_node_id": end.get("id", ""),
            "_alts_next": [],
        })
        end_index[end["id"]] = len(params) - 1

    # --- другий прохід: підставити числові nextContentId ---
    for p in params:
        for alt in p.get("_alts_next", []):
            nxt = alt.get("nextContentId", "")
            if nxt in node_index:
                alt["nextContentId"] = node_index[nxt]
            elif nxt in end_index:
                alt["nextContentId"] = end_index[nxt]
            else:
                alt["nextContentId"] = -1    # недійсний зв'язок -> кінець
        # прибрати службові поля
        p.pop("_node_id", None)
        p.pop("_alts_next", None)

    start_id = node_index.get(tree["nodes"][0]["id"], 0) if tree.get("nodes") else 0
    h5p = {
        "branchingScenario": {
            "content": params,
            "startScreen": {
                "startScreenTitle": tree.get("title", "Сценарій"),
                "startScreenSubtitle": " / ".join(tree.get("objectives", [])[:3]),
            },
            "endScreens": [
                {"endScreenTitle": e.get("title", ""),
                 "endScreenSubtitle": e.get("summary", ""),
                 "contentId": end_index[e["id"]]}
                for e in tree.get("ends", []) if e["id"] in end_index
            ],
            "scoreOption": "static-end-score",
            "startContentId": start_id,
        },
        "behaviour": {"enableScores": True,
                      "randomizeBranchingQuestions": False},
    }
    return h5p


def export_h5p(tree: dict) -> str:
    """Повертає JSON-рядок content.json для H5P Branching Scenario."""
    return json.dumps(tree_to_h5p(tree), ensure_ascii=False, indent=2)


def build_h5p_package(tree: dict) -> bytes:
    """Будує повний пакет .h5p (ZIP), який Moodle/H5P.com приймає напряму.

    Структура пакета (стандарт H5P):
      h5p.json            — маніфест (title, language, mainLibrary,
                            preloadedDependencies)
      content/content.json— параметри контенту (branchingScenario)

    Голий content.json Moodle НЕ імпортує — потрібен саме ZIP-пакет
    із розширенням .h5p і маніфестом h5p.json у корені.
    """
    import io
    import zipfile

    content_json = json.dumps(tree_to_h5p(tree), ensure_ascii=False,
                              indent=2)
    title = (tree.get("title") or "Branching Scenario")[:255]
    manifest = {
        "title": title,
        "language": "uk",
        "mainLibrary": "H5P.BranchingScenario",
        "embedTypes": ["div"],
        "license": "U",
        "defaultLanguage": "uk",
        "preloadedDependencies": [
            {"machineName": "H5P.BranchingScenario",
             "majorVersion": 1, "minorVersion": 7},
            {"machineName": "H5P.BranchingQuestion",
             "majorVersion": 1, "minorVersion": 0},
            {"machineName": "H5P.AdvancedText",
             "majorVersion": 1, "minorVersion": 1},
        ],
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("h5p.json",
                   json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("content/content.json", content_json)
    return buf.getvalue()


def export_h5p_file(tree: dict, path: str) -> str:
    """Записує готовий пакет .h5p на диск. Повертає шлях."""
    data = build_h5p_package(tree)
    with open(path, "wb") as f:
        f.write(data)
    return path


def export_json(tree: dict) -> str:
    """Повертає універсальний JSON сценарію (чиста структура дерева)."""
    doc = {
        "format": "branching-scenario/1.0",
        "title": tree.get("title", ""),
        "objectives": tree.get("objectives", []),
        "nodes": tree.get("nodes", []),
        "ends": tree.get("ends", []),
        "guide": tree.get("guide", {}),
        "gift": tree.get("gift", ""),
    }
    return json.dumps(doc, ensure_ascii=False, indent=2)


def tree_to_outline(tree: dict) -> str:
    """Render the parsed scenario as an indented hierarchical outline
    (читабельне дерево без розмітки)."""
    out = []
    out.append(f"■ {tree['title'] or 'Сценарій'}")
    if tree["objectives"]:
        out.append("  Навчальні цілі:")
        for o in tree["objectives"]:
            out.append(f"    • {o}")
    for n in tree["nodes"]:
        out.append(f"\n  ┌─ {n['id']}")
        if n["situation"]:
            out.append(f"  │  {n['situation']}")
        out.append(f"  │  ❓ {n['question']}")
        for o in n["options"]:
            sign = "+" if o["score_change"] > 0 else ""
            out.append(f"  │    {o['label']}) {o['text']}")
            out.append(f"  │        → {o['next_node']} "
                       f"[{sign}{o['score_change']}]")
    if tree["ends"]:
        out.append("\n  Кінцівки:")
        for e in tree["ends"]:
            out.append(f"    ▣ {e['id']} — {e['title']} [{e['type']}] "
                       f"(бали: {e['range']})")
    return "\n".join(out)
