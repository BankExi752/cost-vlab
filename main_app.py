# -*- coding: utf-8 -*-
"""智控成本 · 数创价值 —— 制造企业全流程成本管理虚拟仿真决策实训
====================================================
Streamlit 教学应用 V4.0（2026 中国仿真创新应用大赛 · 仿真教学应用赛道 · 虚拟仿真实验设计方向）

依据《智控成本数创价值_设计方案_V4.0》实现：
- 25 步决策主线交互式仿真实验（模块A 成本核算基本功 10 步 / 模块B 两法对比与决策 9 步 / 模块C 作业责任与降本 6 步）+ 复盘报告/能力画像/经营决策报告三大输出板块；
- 算账闭环四指标：单位产品成本、经营利润、成本偏离指数、责任绩效分，每步操作后实时刷新；
- 红线机制（3 条 · 两次触发制）：成本造假 / 虚增存货 / 责任甩锅；
- 5 类风险事件随机触发（含二次确认），参数化决策影响成本与利润；
- AI 能力（本地规则引擎降级）：金点子方案评判（四维加权）+ 每步提分建议；
- 全局易用性：25 步进度导航、右侧四指标面板、里程碑鼓励、3 次悔棋、8 个小白化词条、
  同口径复盘、五维能力雷达、经营决策报告书、教师模式（成绩导出）。

算账引擎为模块级纯函数（可冒烟测试）；UI 层以 st.session_state 驱动。
"""
import copy
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "V4.0"

# ============================================================================
# 一、元数据：25 步主线 + 三大输出板块、模块、术语
# ============================================================================
MODULES = [
    ("A", "模块A · 成本核算基本功", "1 课时"),
    ("B", "模块B · 两法对比与决策", "1 课时"),
    ("C", "模块C · 作业责任与降本", "1 课时"),
]

# (序号, 名称, 模块, 交互类型, 算账影响)
STEPS = [
    (1,  "开局签约 · 目标利润率",         "A", "滑块+卡片", "初始化目标利润"),
    (2,  "采购 · 选供应商",               "A", "卡片",       "材料单价、返工成本"),
    (3,  "入库 · 材料单价与采购量",       "A", "滑块",       "直接材料成本"),
    (4,  "领料 · 投料方式",               "A", "卡片",       "在产品成本"),
    (5,  "人工 · 工时与工资率",           "A", "滑块",       "直接人工"),
    (6,  "混合成本分解",                  "A", "滑块+图表",  "固定/变动成本拆分"),
    (7,  "制造费用 · 分摊基数",           "A", "卡片",       "制造费用分摊"),
    (8,  "辅助生产分配",                  "A", "卡片+滑块",  "辅助车间费用"),
    (9,  "约当产量 · 完工程度",           "A", "滑块",       "完工/在产成本"),
    (10, "品种法 · 成本计算单",           "A", "输入+比对",  "单位成本"),
    (11, "分批法 · 批次成本",             "B", "输入+卡片",  "批次毛利"),
    (12, "分步法 · 成本还原计算器",       "B", "输入+计算器", "最终单位成本"),
    (13, "两法切换 · 变动/完全成本法",    "B", "卡片",       "存货吸收固定成本"),
    (14, "量本利分析",                    "B", "滑块",       "保本点、经营利润"),
    (15, "产销情境",                      "B", "卡片",       "利润差"),
    (16, "存货计价",                      "B", "卡片",       "存货价值、利润"),
    (17, "标准成本设定",                  "B", "滑块",       "成本偏离指数"),
    (18, "差异分析 · 责任归属",           "B", "卡片",       "责任中心超支"),
    (19, "金点子 · 降本增效方案",         "C", "输入框+AI判分", "创新分"),
    (20, "作业成本法 · 动因选择",         "C", "卡片",       "间接费用重摊"),
    (21, "动因博弈",                      "C", "卡片+输入",  "核算精度vs短期利润"),
    (22, "责任中心划分",                  "C", "卡片",       "责任绩效分"),
    (23, "数据仪表盘",                    "C", "可视化看板", "无操作，只看"),
    (24, "风险事件应对",                  "C", "卡片",       "风险损失"),
    (25, "红线检查",                      "C", "系统判定",   "触红线=失败"),
    (26, "同口径复盘",                    "C", "复盘表",     "改进建议"),
    (27, "能力画像 · 五维雷达",           "C", "自动生成",   "终结性评分"),
    (28, "经营决策报告",                  "C", "输出报告",   "终结性评分"),
]
STEP_FULL = 28
# 决策台主线步骤 = 第 1-25 步（26/27/28 为独立输出板块，不属于步骤导航）
MAIN_STEPS = [s0 for s0 in STEPS if s0[0] <= 25]
MAIN_FULL = 25

# 侧边栏导航短名（简短好看，pills 短标签用）
NAV_SHORT = {
    1: "签约", 2: "采购", 3: "入库", 4: "领料", 5: "人工",
    6: "混合成本", 7: "制造费用", 8: "辅助分配", 9: "约当产量", 10: "品种法",
    11: "分批法", 12: "分步法", 13: "两法切换", 14: "量本利", 15: "产销情境",
    16: "存货计价", 17: "标准成本", 18: "差异分析", 19: "金点子",
    20: "作业成本", 21: "动因博弈", 22: "责任中心", 23: "仪表盘",
    24: "风险应对", 25: "红线检查", 26: "复盘", 27: "能力画像", 28: "决策报告",
}
MODULE_ACCENTS = {"A": "#0b3d91", "B": "#1f6feb", "C": "#2e9e5b"}

# 顶部板块导航（参照"实验导览/决策台/复盘报告"式独立板块布局）
# 主线决策台 = 第 1-25 步（24 步决策 + 第 25 步红线检查）；26/27/28 为独立输出板块
PAGES = [("🗺️ 实验导览", "导览"), ("🧭 决策台（25步）", "决策台"),
         ("📋 复盘报告", "复盘"), ("🛡️ 能力画像", "画像"), ("📊 经营决策报告", "报告")]
PAGE_BY_LABEL = dict(PAGES)                    # 板块名 → page id
PAGE_BY_ID = dict((p, t) for t, p in PAGES)    # page id → 板块名
BOARD_NAMES = {26: "📋 复盘报告 · 同口径复盘",
               27: "🛡️ 能力画像 · 五维雷达",
               28: "📊 经营决策报告 · 定价/排产/考核建议"}


def _nav_cb(page_id):
    """板块切换回调：在 widget 实例化前运行，可安全更新导航高亮"""
    st.session_state.page = page_id
    st.session_state["top_nav"] = PAGE_BY_ID[page_id]


def main_done():
    """主线（决策台 1-25 步）是否完成"""
    return all(i in st.session_state.decisions for i in range(1, 26))
MILESTONES = {5: "已完成 5/25！你已掌握成本核算的开局要领。",
              10: "已完成 10/25！你已掌握成本核算核心方法，进入两法对比阶段。",
              15: "已完成 15/25！两法对比与差异分析已过半，继续加油。",
              20: "已完成 20/25！作业成本与责任考核阶段开始发力。",
              25: "已完成 25/25！决策台主线收官，前往复盘报告/能力画像/经营决策报告三大板块完成闭环输出。"}

RED_LINE_NAMES = ["成本造假", "虚增存货", "责任甩锅"]
RED_LINE_TRIGGER_STEP = {"成本造假": 3, "虚增存货": 9, "责任甩锅": 22}

# 8 个小白化词条：一句话解释 + 真实案例 + 具体样例
GLOSSARY = {
    "约当产量": {"explain": "把未完工的在产品，按完工程度折算成相当于多少件完工产品，才能和完工产品一起分摊成本。",
                 "case": "车间有 100 件衣服只缝了一半袖子，2 件半成品 ≈ 1 件成品。",
                 "sample": "在产品 100 件、加工完工程度 50% → 加工约当产量 = 100×50% = 50 件。"},
    "成本还原": {"explain": "分步法下，把上一车间转来的'半成品'成本，拆回它本来的材料、人工、制造费用，避免成本层层'打包'失真。",
                 "case": "买来的蛋糕胚 10 元，其中面粉 6 元、人工 4 元——算总成本时要拆开看。",
                 "sample": "半成品 200 件 × 单位 350 元 × 材料还原率 60% → 还原出直接材料 42000 元。"},
    "固定制造费用库存吸收": {"explain": "完全成本法把固定制造费用摊进存货，产量越大单位成本越低；变动成本法则把固定制造费用全部当期计入损益。",
                 "case": "厂房租金是固定的，多生产 100 件，每件摊到的租金就少了。",
                 "sample": "变动成本法下利润 = (售价−单位变动成本)×销量 − 固定制造费用总额。"},
    "作业动因": {"explain": "导致一项作业成本发生变化的真正原因，比如'检验次数''生产批次'，用它把间接费用合理分给产品。",
                 "case": "质检成本跟检验批次走，而不是跟产量走。",
                 "sample": "A 产品检验 10 批、B 产品 5 批，质检费按 2:1 分摊。"},
    "责任中心": {"explain": "把企业切成若干'承包单元'，每个单元对自己能控制的成本/利润负责，便于考核谁干得好。",
                 "case": "生产车间管成本（成本中心），销售部管收入利润（利润中心）。",
                 "sample": "价格差异归采购中心、用量差异归生产中心——不甩锅。"},
    "标准成本差异": {"explain": "实际成本与事先定的'标准成本'的差距，差距=价格/用量/效率差异，用来定位超支源头。",
                 "case": "预算 10 元/件的材料，实际花了 12 元，多出的 2 元要查是买贵了还是用多了。",
                 "sample": "成本偏离指数 = 实际单位成本 ÷ 标准单位成本 × 100%，105% 以上亮黄/红。"},
    "混合成本分解": {"explain": "把同时含固定和变动部分的水电费等'混合成本'，用高低点法或回归法拆成'固定部分+变动率×业务量'。",
                 "case": "电费 = 基础照明费（固定）+ 每台机器耗电（变动）。",
                 "sample": "高低点法：变动成本率 = (最高费用−最低费用) ÷ (最高产量−最低产量)。"},
    "存货计价": {"explain": "先进先出/加权平均/个别计价是计算'发出存货成本'的三种规则，影响销货成本和利润。",
                 "case": "进货价一路上涨时，先进先出会让当期利润显得更高。",
                 "sample": "加权平均单价 = 总成本 ÷ 总数量，发出成本 = 加权平均单价 × 发出数量。"},
}

# ============================================================================
# 二、算账引擎（纯函数，可脱离 UI 冒烟测试）
# ============================================================================

def calc_material_equiv(wip_qty, material_pct):
    """材料约当产量 = 在产品数量 × 材料完工程度"""
    return wip_qty * material_pct


def calc_processing_equiv(wip_qty, processing_pct):
    """加工约当产量 = 在产品数量 × 加工完工程度"""
    return wip_qty * processing_pct


def engine_calc(material_total, processing_total, finished_qty, wip_qty,
                material_pct, processing_pct):
    """核心算账：返回单位成本、完工/在产品成本等（教材标准口径）。

    材料单位成本 = 直接材料总额 / (完工数量 + 材料约当产量)
    加工单位成本 = 加工成本总额 / (完工数量 + 加工约当产量)
    单位产品成本 = 材料单位成本 + 加工单位成本
    """
    mat_equiv = calc_material_equiv(wip_qty, material_pct)
    proc_equiv = calc_processing_equiv(wip_qty, processing_pct)
    denom_m = finished_qty + mat_equiv
    denom_p = finished_qty + proc_equiv
    mat_unit = material_total / denom_m
    proc_unit = processing_total / denom_p
    unit_cost = mat_unit + proc_unit
    finished_cost = unit_cost * finished_qty
    wip_cost = mat_unit * mat_equiv + proc_unit * proc_equiv
    return {
        "mat_equiv": mat_equiv, "proc_equiv": proc_equiv,
        "mat_unit": mat_unit, "proc_unit": proc_unit,
        "unit_cost": unit_cost,
        "finished_cost": finished_cost, "wip_cost": wip_cost,
        "total_cost": finished_cost + wip_cost,
    }


def deviation_color(idx):
    """≤95% 蓝 / 95-105% 绿 / 105-115% 黄 / >115% 红"""
    if idx <= 95:
        return "蓝"
    if idx <= 105:
        return "绿"
    if idx <= 115:
        return "黄"
    return "红"


def perf_score(deviation_idx):
    """责任绩效分 = 95 − |偏离指数−100|×2，0-100 分（低于95%同样扣分，防偷工减料）"""
    return max(0.0, min(100.0, 95.0 - abs(deviation_idx - 100.0) * 2.0))


def compute_indicators(cfg, red_line_counts):
    """由配置计算四指标（含红线扣分）。cfg 见 get_cfg()。"""
    r = engine_calc(cfg["material_total"], cfg["processing_total"],
                    cfg["finished_qty"], cfg["wip_qty"],
                    cfg["mat_pct"], cfg["proc_pct"])
    unit_cost = r["unit_cost"]
    # 经营利润：完全成本法 售价×销量 − 已销产品成本；变动成本法 (售价−单位变动)×销量 − 固定制造费用
    if cfg["cost_method"] == "变动成本法":
        var_unit = cfg["mat_unit_var"] + cfg["labor_unit"]
        profit = (cfg["selling_price"] - var_unit) * cfg["sales_qty"] - cfg["overhead"]
        sales_cost = var_unit * cfg["sales_qty"] + cfg["overhead"]
    else:
        # 产销平衡时无期末存货，存货计价不影响已销成本；存在存货时（产销不平衡）才应用计价系数
        adj = cfg["inv_adj"] if cfg["finished_qty"] > cfg["sales_qty"] else 1.0
        profit = cfg["selling_price"] * cfg["sales_qty"] - unit_cost * cfg["sales_qty"] * adj
        sales_cost = unit_cost * cfg["sales_qty"] * adj
    deviation = unit_cost / cfg["std_unit"] * 100.0 if cfg["std_unit"] else 100.0
    perf = perf_score(deviation) - 30.0 * sum(red_line_counts.values())
    perf = max(0.0, min(100.0, perf))
    inventory_val = max(0.0, cfg["finished_qty"] - cfg["sales_qty"]) * unit_cost
    breakeven_qty = cfg["overhead"] / max(1e-6, cfg["selling_price"] - (cfg["mat_unit_var"] + cfg["labor_unit"]))
    return {
        "unit_cost": unit_cost, "profit": profit, "deviation": deviation,
        "deviation_color": deviation_color(deviation), "perf": perf,
        "sales_cost": sales_cost, "inventory_val": inventory_val,
        "breakeven_qty": breakeven_qty,
        "mat_unit": r["mat_unit"], "proc_unit": r["proc_unit"],
        "finished_cost": r["finished_cost"], "wip_cost": r["wip_cost"],
        "total_cost": r["total_cost"],
    }


def red_line_status(cfg, decisions):
    """返回当前触发中的红线列表"""
    lines = []
    if decisions.get(3, {}).get("unit_price", 12.0) > 20:
        lines.append("成本造假")
    if cfg["wip_qty"] > cfg["finished_qty"] * 2:
        lines.append("虚增存货")
    if decisions.get(22, {}).get("center_choice", "") == "全部推给他方":
        lines.append("责任甩锅")
    return lines


# ---------- AI：金点子四维判定（本地规则引擎，降级路径三·预设评语库） ----------
AI_DIMS = {
    "创新性": (["智能", "数字化", "系统", "监控", "平台", "算法", "自动", "优化", "创新",
                "模式", "共享", "协同", "大数据", "物联网", "绿色", "低碳", "转型", "升级",
                "追溯", "传感"], 30, 10.0),
    "可操作性": (["步骤", "流程", "实施", "阶段", "落地", "方案", "预算", "计划", "排期",
                  "分工", "节点", "跟踪", "试点", "培训", "月度", "周报", "负责人"], 30, 10.0),
    "成本影响": (["降本", "成本", "费用", "节约", "节省", "下降", "减少", "万元", "材料",
                  "人工", "库存", "报废", "损耗", "能耗", "电费", "废品", "效率", "良率"], 25, 8.0),
    "业财融合": (["财务", "会计", "核算", "预算", "绩效", "指标", "分析", "业财",
                  "报表", "考核", "管控", "收益", "利润", "数据"], 15, 5.0),
}


def ai_score_idea(text):
    """金点子评判：创新性30% + 可操作性30% + 成本影响25% + 业财融合15%，0-100 分"""
    t = (text or "").lower()
    dims = {}
    for name, (keywords, weight, base) in AI_DIMS.items():
        hits = sum(1 for kw in keywords if kw in t)
        dims[name] = min(weight, base + hits * (weight / 6.0))
    score = min(100.0, sum(dims.values()))
    if len(t) < 12:
        score = min(score, 40.0)
        comment = "方案过于简短，请补充具体措施与预期效果（当前按 40 分封顶）。"
    elif score >= 85:
        comment = "方案创新且可落地，成本影响与业财融合清晰，属于优秀提案。"
    elif score >= 70:
        comment = "方案较完整，建议进一步量化成本节约金额并明确责任与排期。"
    elif score >= 50:
        comment = "方案具备雏形，但创新性/可操作性需加强，建议补充具体工具与实施步骤。"
    else:
        comment = "方案偏空泛，请围绕'降本+核算+决策'补充可量化、可执行的措施。"
    return round(score, 1), comment, dims


def ai_step_advice(step, before, after, cfg, decisions):
    """每步操作后基于四指标变化的提分建议（规则引擎，非通用套话）"""
    out = []
    if after["deviation"] > 105:
        out.append(f"成本偏离指数已达 {after['deviation']:.1f}%（黄/红区），建议回到步3压低材料单价，或调整步7分摊基数、步8辅助分配比例，先控总量。")
    elif after["deviation"] < 95:
        out.append(f"成本偏离指数 {after['deviation']:.1f}%（蓝区，低于标准5%+），注意防止'偷工减料'式误判，可在步19金点子中说明低成本策略的合理性。")
    if after["profit"] < 0:
        out.append(f"当前经营利润为负（{after['profit']:,.0f} 元），优先在步14提价或压缩变动成本，步15保持产销平衡，避免存货积压吃掉利润。")
    if after["perf"] < 80:
        out.append(f"责任绩效分 {after['perf']:.1f}（低于80），回看步18差异归属与步22责任中心划分，把差异落到正确责任主体上。")
    if step == 6 and not decisions.get(6, {}).get("ok", True):
        out.append("步6混合成本分解偏差已计入制造费用：建议改用高低点法，用（最高−最低）费用差÷产量差重新验算变动成本率。")
    if step == 9 and cfg["wip_qty"] > cfg["finished_qty"]:
        out.append("步9在产品数量偏高（虚增存货红线=在产品＞完工×2），注意约当产量口径，避免存货虚增。")
    if step == 20 and not decisions.get(20, {}).get("ok", True):
        out.append("步20作业动因选择与作业特性不匹配导致间接费用重摊失真，请按'成本动因'重新选择。")
    if not out:
        out.append("四项指标平稳，可把精力放到金点子与经营决策报告的创新性上，冲刺更高评价。")
    return out[:3]


# ============================================================================
# 三、状态管理与配置
# ============================================================================
DEFAULTS = {
    "unit_price": 12.0, "qty": 5000, "coef": 1.0,
    "hours": 2000, "wage": 25.0, "overhead": 45000.0,
    "finished_qty": 300, "wip_qty": 100, "mat_pct": 1.0, "proc_pct": 0.5,
    "selling_price": 600.0, "sales_qty": 300,
    "cost_method": "完全成本法", "inv_adj": 1.0,
    "target_margin": 0.15,
}

SUPPLIERS = {
    "均衡供应商": {"price": 12.0, "coef": 1.00, "desc": "价格适中、交期5天、质量合格，综合性价比最优（推荐⭐）"},
    "低价供应商": {"price": 11.0, "coef": 0.90, "desc": "单价低1元，但质量偏低（质量系数0.9），返工风险高"},
    "优质供应商": {"price": 13.5, "coef": 1.08, "desc": "单价高1.5元，质量优质（质量系数1.08），交期7天"},
}


def init_state():
    s = st.session_state
    if "started" in s:
        return
    s.started = True
    s.page = "导览"           # 顶部板块：导览 / 决策台 / 复盘 / 画像 / 报告
    s.current_step = 1
    s.decisions = {}
    s.step_ok = {}
    s.indicators = None
    s.prev_indicators = None
    s.red_lines = {ln: 0 for ln in RED_LINE_NAMES}
    s.red_prev = {ln: False for ln in RED_LINE_NAMES}
    s.terminated = False
    s.history = []          # 每步指标快照 [{step, unit_cost, profit, deviation, perf}]
    s.undo_stack = []       # [(completed_step, snapshot)]
    s.undo_left = 3
    s.ai_advice = {}
    s.milestone = None
    s.scores = {"核算准确": 0.0, "成本分析": 0.0, "决策能力": 0.0,
                "业财融合": 0.0, "创新意识": 0.0}
    s.risk_event_id = None
    s.start_time = time.time()
    s.final_report = None


def snap():
    s = st.session_state
    return copy.deepcopy({
        "decisions": s.decisions, "step_ok": s.step_ok, "red_lines": s.red_lines,
        "red_prev": s.red_prev, "terminated": s.terminated, "history": s.history,
        "ai_advice": s.ai_advice, "milestone": s.milestone, "scores": s.scores,
        "indicators": s.indicators, "prev_indicators": s.prev_indicators,
        # 注意：不复制 undo_stack 自身，避免快照嵌套导致 O(n²) 膨胀
    })


def restore(snap_dict):
    s = st.session_state
    for k, v in snap_dict.items():
        s[k] = v


def get_cfg():
    """由 decisions 组装当前全部成本参数"""
    d = st.session_state.decisions
    g = lambda step, key, default: d.get(step, {}).get(key, default)
    cfg = dict(DEFAULTS)
    cfg["target_margin"] = g(1, "target_margin", 0.15)
    sup = SUPPLIERS.get(g(2, "supplier", "均衡供应商"), SUPPLIERS["均衡供应商"])
    cfg["coef"] = sup["coef"]
    cfg["unit_price"] = g(3, "unit_price", 12.0)
    cfg["qty"] = g(3, "qty", 5000)
    cfg["hours"] = g(5, "hours", 2000)
    cfg["wage"] = g(5, "wage", 25.0)
    cfg["mat_pct"] = 1.0 if g(4, "feed", "一次投入") == "一次投入" else 0.5
    cfg["wip_qty"] = g(9, "wip_qty", 100)
    cfg["proc_pct"] = g(9, "proc_pct", 50) / 100.0
    cfg["finished_qty"] = DEFAULTS["finished_qty"]
    cfg["selling_price"] = g(14, "price", 600.0)
    cfg["sales_qty"] = g(14, "sales_qty", 300)
    scen = g(15, "scenario", None)
    if scen == "存货增加":
        cfg["sales_qty"] = 250
    elif scen == "销售下滑":
        cfg["sales_qty"] = 200
    cfg["cost_method"] = g(13, "cost_method", "完全成本法")
    cfg["inv_adj"] = {"先进先出": 0.98, "加权平均": 1.0, "个别计价": 1.02}.get(
        g(16, "inv_method", "先进先出"), 1.0)
    # 步6/8/20/21 分解与动因质量对制造费用的影响
    overhead = 45000.0
    if not g(6, "ok", True):
        overhead += 3000.0
    if not g(8, "ok", True):
        overhead += 2000.0
    if 20 in d and not g(20, "ok", True):
        overhead *= 1.04
    if g(21, "choice", "") == "改":
        overhead *= 1.02
    cfg["overhead"] = overhead
    # 步24 风险事件影响
    r24 = d.get(24, {})
    cfg["mat_mult"] = r24.get("mat_mult", 1.0)
    cfg["price_mult"] = r24.get("price_mult", 1.0)
    cfg["overhead_add"] = r24.get("overhead_add", 0.0)
    cfg["finished_add"] = r24.get("finished_add", 0)
    cfg["proc_mult"] = r24.get("proc_mult", 1.0)
    cfg["sales_mult"] = r24.get("sales_mult", 1.0)
    cfg["quality_mult"] = r24.get("quality_mult", 1.0)
    # 材料与加工
    cfg["material_total"] = cfg["unit_price"] * cfg["qty"] * cfg["coef"] \
        * cfg["mat_mult"] * cfg["quality_mult"]
    cfg["labor_total"] = cfg["hours"] * cfg["wage"]
    cfg["labor_unit"] = cfg["labor_total"] / (cfg["finished_qty"] + cfg["wip_qty"] * cfg["proc_pct"])
    cfg["mat_unit_var"] = cfg["material_total"] / (cfg["finished_qty"] + cfg["wip_qty"] * cfg["mat_pct"])
    cfg["processing_total"] = (cfg["labor_total"] + cfg["overhead"] + cfg["overhead_add"]) * cfg["proc_mult"]
    cfg["finished_qty"] += cfg["finished_add"]
    cfg["sales_qty"] = max(1, int(cfg["sales_qty"] * cfg["sales_mult"]))
    cfg["selling_price"] *= cfg["price_mult"]
    # 标准成本（步17，未设置时用默认，使默认场景落绿区）
    sd = d.get(17, {})
    std_mat = sd.get("std_mat_price", 12.0) * sd.get("std_mat_qty", 5000)
    std_labor = sd.get("std_hours", 2000) * sd.get("std_wage", 27.0)
    std_ovh = sd.get("std_overhead", 40500.0)
    r = engine_calc(std_mat, std_labor + std_ovh, cfg["finished_qty"],
                    cfg["wip_qty"], cfg["mat_pct"], cfg["proc_pct"])
    cfg["std_unit"] = r["unit_cost"]
    return cfg


def compute_scores():
    """五维能力画像（0-100），基于过程表现"""
    s = st.session_state
    d = s.decisions
    ok = s.step_ok
    # 核算准确：步10/11/12
    acc = 55.0 + (15.0 if ok.get(10) else 0.0) + (15.0 if ok.get(11) else 0.0) + (15.0 if ok.get(12) else 0.0)
    # 成本分析：步6/8 正确 + 当前偏离落绿/蓝
    ana = 40.0 + (20.0 if ok.get(6) else 0.0) + (20.0 if ok.get(8) else 0.0)
    if s.indicators and s.indicators["deviation_color"] in ("蓝", "绿"):
        ana += 20.0
    # 决策能力：步15 产销 / 步21 动因 / 步24 风险
    dec = 40.0
    scen = d.get(15, {}).get("scenario", "")
    dec += {"产销平衡": 20.0, "存货增加": 10.0, "销售下滑": 5.0}.get(scen, 0.0)
    dec += 20.0 if d.get(21, {}).get("choice", "") == "改" else (5.0 if d.get(21) else 0.0)
    r24 = d.get(24, {})
    if r24.get("choice_quality"):
        dec += 20.0
    elif r24.get("choice_quality") is not None:
        dec += 8.0
    # 业财融合：步13/16/20/22
    fin = 30.0
    if d.get(13): fin += 10.0
    if d.get(16): fin += 10.0
    if ok.get(20): fin += 25.0
    if d.get(22, {}).get("center_choice", "") != "全部推给他方" and d.get(22): fin += 25.0
    # 创新意识：步19
    inn = d.get(19, {}).get("ai_score", 0.0)
    s.scores = {"核算准确": min(100.0, acc), "成本分析": min(100.0, ana),
                "决策能力": min(100.0, dec), "业财融合": min(100.0, fin),
                "创新意识": min(100.0, inn)}


def finalize(step):
    """步骤确认后的收尾：算账、红线、历史、里程碑、AI 建议"""
    s = st.session_state
    cfg = get_cfg()
    ind = compute_indicators(cfg, s.red_lines)
    s.indicators = ind
    compute_scores()
    # 红线两次触发制
    lines = red_line_status(cfg, s.decisions)
    for ln in RED_LINE_NAMES:
        now = ln in lines
        if now and not s.red_prev[ln] and RED_LINE_TRIGGER_STEP[ln] == step:
            s.red_lines[ln] += 1
            if s.red_lines[ln] >= 2:
                s.terminated = True
        s.red_prev[ln] = now
    s.history.append({"step": step, "unit_cost": ind["unit_cost"], "profit": ind["profit"],
                      "deviation": ind["deviation"], "perf": ind["perf"]})
    s.undo_stack.append((step, snap()))
    if step in MILESTONES:
        s.milestone = (step, MILESTONES[step])
    before = s.prev_indicators
    s.ai_advice[step] = ai_step_advice(step, before, ind, cfg, s.decisions)
    s.prev_indicators = ind


def undo():
    s = st.session_state
    if s.undo_left <= 0 or s.current_step <= 2:
        return False
    target = max(1, s.current_step - 5)
    entry = None
    for stp, snapd in s.undo_stack:
        if stp == target:
            entry = snapd
    if entry is None:
        return False
    # 回退时保留 undo 历史：把回退点之后的历史裁剪掉
    keep = [x for x in s.undo_stack if x[0] <= target]
    restore(entry)
    s.undo_stack = keep
    s.undo_left -= 1
    s.current_step = target + 1
    return True


def risk_events_pool():
    return [
        {"id": "E1", "name": "原材料涨价 20%",
         "desc": "供应商通知：核心原材料采购价上涨 20%，你将如何应对？",
         "options": [
             {"label": "接受涨价", "desc": "按新价格采购，材料成本 +20%", "fx": {"mat_mult": 1.2}, "q": 50},
             {"label": "更换供应商", "desc": "更换备选供应商，成本 +8%，但质量系数降 5%", "fx": {"mat_mult": 1.08, "quality_mult": 0.95}, "q": 80},
             {"label": "锁价谈判", "desc": "与供应商锁价，成本仅 +10%，需消耗管理精力", "fx": {"mat_mult": 1.10}, "q": 70},
         ]},
        {"id": "E2", "name": "紧急订单插单",
         "desc": "大客户紧急插单，要求 3 天内交付额外 50 件，你如何决策？",
         "options": [
             {"label": "接受插单", "desc": "追加生产 40 件，但整体售价折扣 5%", "fx": {"finished_add": 40, "price_mult": 0.95}, "q": 70},
             {"label": "拒绝插单", "desc": "保现有订单节奏，客户满意度下降（责任绩效 -5）", "fx": {"perf_penalty": 5}, "q": 40},
         ]},
        {"id": "E3", "name": "设备突发故障（产能 -30%）",
         "desc": "关键设备突发故障，产能下降 30%，本月订单面临延期风险。",
         "options": [
             {"label": "加班赶工", "desc": "安排加班，制造费用 +8000 元", "fx": {"overhead_add": 8000}, "q": 60},
             {"label": "延期交付", "desc": "与客户协商延期，支付违约金 5000 元", "fx": {"overhead_add": 5000}, "q": 45},
             {"label": "外包加工", "desc": "部分工序外包，加工成本 +10%", "fx": {"proc_mult": 1.10}, "q": 80},
         ]},
        {"id": "E4", "name": "质检发现批量不合格品",
         "desc": "质检抽检发现一批产品不合格，占产量 8%，如何处理？",
         "options": [
             {"label": "全数返工", "desc": "全数返工，加工成本 +6000 元", "fx": {"overhead_add": 6000}, "q": 60},
             {"label": "降价处理", "desc": "按不合格品降价 8% 出售", "fx": {"price_mult": 0.92}, "q": 45},
         ]},
        {"id": "E5", "name": "客户要求降价 10%",
         "desc": "核心客户要求下季度价格下调 10%，否则转投竞对。",
         "options": [
             {"label": "接受降价", "desc": "售价 -10%，保住大客户订单", "fx": {"price_mult": 0.90}, "q": 55},
             {"label": "拒绝降价", "desc": "维持价格，预计销量下降 20%", "fx": {"sales_mult": 0.80}, "q": 40},
         ]},
    ]


# ============================================================================
# 四、可视化（plotly）
# ============================================================================
def plot_cost_pie(cfg):
    fig = go.Figure(go.Pie(
        labels=["直接材料", "直接人工", "制造费用"],
        values=[cfg["material_total"], cfg["labor_total"],
                cfg["overhead"] + cfg["overhead_add"]],
        hole=0.4,
        marker=dict(colors=["#1E88E5", "#7C4DFF", "#00A86B"])))
    fig.update_layout(title="成本结构占比（当前配置）", height=300,
                      margin=dict(l=20, r=20, t=40, b=10))
    return fig


def plot_profit_line(history):
    xs = [h["step"] for h in history]
    ys = [h["profit"] for h in history]
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers",
                               line=dict(color="#1E88E5", width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(title="经营利润随步骤变化趋势", xaxis_title="步骤", yaxis_title="利润（元）",
                      height=300, margin=dict(l=20, r=20, t=40, b=10))
    return fig


def plot_deviation_bar(history):
    xs = [h["step"] for h in history]
    ys = [h["deviation"] for h in history]
    colors = [{"蓝": "#1E88E5", "绿": "#00A86B", "黄": "#F9A825", "红": "#E53935"}[
        deviation_color(v)] for v in ys]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors))
    fig.add_hline(y=95, line_dash="dot", line_color="#1E88E5")
    fig.add_hline(y=105, line_dash="dot", line_color="#F9A825")
    fig.add_hline(y=115, line_dash="dot", line_color="#E53935")
    fig.update_layout(title="成本偏离指数逐步骤（蓝≤95 / 绿95-105 / 黄105-115 / 红>115）",
                      xaxis_title="步骤", yaxis_title="偏离指数 %",
                      height=300, margin=dict(l=20, r=20, t=40, b=10))
    return fig


def plot_radar(scores):
    labels = list(scores.keys())
    values = [scores[k] for k in labels]
    fig = go.Figure(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1],
                                    fill="toself", line=dict(color="#7C4DFF", width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                      title="五维能力画像", height=360,
                      margin=dict(l=40, r=40, t=50, b=20))
    return fig


# ============================================================================
# 五、25 步主线渲染（26/27/28 为独立板块）
# ============================================================================
def step_header(no, name):
    """步骤标题横幅：模块主题色渐变 + 交互/算账影响说明"""
    mod = dict((s[0], s[2]) for s in STEPS)[no]
    accent = MODULE_ACCENTS[mod]
    st.markdown(
        f'<div style="background:linear-gradient(120deg,{accent} 0%,#2f7cf6 100%);'
        f'border-radius:14px;padding:14px 20px;color:#fff;margin:8px 0 14px;'
        f'box-shadow:0 4px 14px rgba(11,61,145,0.18)">'
        f'<div style="font-size:21px;font-weight:700;letter-spacing:0.5px">第 {no} 步 · {name}</div>'
        f'<div style="font-size:12.5px;opacity:0.92;margin-top:4px;line-height:1.6">'
        f'模块{mod} · 交互：{dict((s[0], s[3]) for s in STEPS)[no]} · 算账影响：{dict((s[0], s[4]) for s in STEPS)[no]}</div></div>',
        unsafe_allow_html=True)
    if st.session_state.indicators is not None and st.session_state.current_step == no:
        pass


def finish_button(no, decision, ok=None, disabled=False):
    s = st.session_state
    if disabled:
        st.button("该步骤不可修改（红线检查）", disabled=True, key=f"fin_{no}")
        return
    if st.button("✅ 确认并进入下一步", type="primary", key=f"fin_{no}"):
        s.decisions[no] = decision
        if ok is not None:
            s.step_ok[no] = ok
        finalize(no)
        if no < STEP_FULL:
            s.current_step = no + 1
        else:
            s.current_step = STEP_FULL
        st.rerun()


def safe_eval_expr(expr: str):
    """安全计算四则运算表达式：AST 白名单求值，不使用 eval。"""
    import ast
    expr = (expr or "").strip()
    if not expr:
        return None
    allowed = (ast.Expression, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
               ast.UnaryOp, ast.USub, ast.UAdd, ast.Constant)
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            return None
    try:
        return eval(compile(tree, "<calc>", "eval"))
    except (ZeroDivisionError, TypeError, OverflowError):
        return None


# 需要计算的步骤 → 本步公式参考（提示语）
CALC_HINTS = {
    3: "材料金额 = 单价（元/kg） × 采购量（kg） × 质量系数（1.00）。如 11*5000",
    5: "直接人工 = 生产工时（h） × 工资率（元/h）。如 2000*25",
    6: "高低点法：b =（最高费用 − 最低费用）÷（最高产量 − 最低产量）= (64000-52000)/(1000-700) → 40；固定成本 a = 64000 - 40*1000 → 24000",
    8: "供电→基本生产 = 6000 × 分配比例。如 6000*0.6 → 3600；供电→管理 = 6000-3600",
    9: "加工约当产量 = 在产品 × 完工程度；约当总产量 = 完工 300 + 加工约当 + 材料约当。如 100*0.5 → 50",
    10: "品种法单位成本 =（材料总额 + 加工总额）÷ 约当总产量。可先算总额再算单位成本",
    11: "批次成本 = 材料 + 人工 + 制造费用。如 A：25000+15000+10000 → 50000；B：20000+12000+8000 → 40000",
    12: "还原材料成本 = 半成品数量 × 单位成本 × 还原率。如 200*350*0.6 → 42000",
    16: "加权平均单位成本 = 可供销售总成本 ÷ 可供销售总数量；已销成本 = 单位成本 × 销量",
    17: "变动成本法利润 =（售价 − 单位变动成本）× 销量 − 固定制造费用。如 (600-330)*300-24000 → 57000",
    20: "作业分配率 = 作业成本 ÷ 作业动因总量；产品应负担 = 分配率 × 该产品动因量",
}


def render_calculator(hint: str):
    """步骤旁计算器：学生可直接输入算式即时计算（支持 + - * / 与括号）。"""
    with st.expander("🧮 计算器（本步公式参考）", expanded=True):
        st.caption(hint)
        expr = st.text_input("算式（回车即算）", key="calc_expr",
                             placeholder="如 2000*25 或 (64000-52000)/(1000-700)")
        if expr.strip():
            res = safe_eval_expr(expr)
            if res is None:
                st.warning("算式无法识别：仅支持数字与 + - * / ( ) ，请检查后重试。")
            elif isinstance(res, float):
                txt = f"{res:,.4f}".rstrip("0").rstrip(".")
                st.success(f"结果：**{txt}**")
            else:
                st.success(f"结果：**{res:,}**")


def render_step1():
    s = st.session_state
    prev = s.decisions.get(1, {})
    step_header(1, "开局签约 · 目标利润率")
    st.markdown("**场景**：与董事会签订年度经营目标。请设定本财年的目标利润率，它将作为「经营决策报告」板块的考核基准。")
    margin = st.slider("目标利润率（%）", 5, 30, int(prev.get("target_margin", 0.15) * 100), 1,
                       help="建议 10%-20%。目标定得过高会挤压后续决策空间，过低则考核无挑战。",
                       key="s1_margin")
    st.markdown("**签约条款**：期末实际利润率 ≥ 目标利润率 视为达成经营目标，未达成将影响终结性评价。")
    finish_button(1, {"target_margin": margin / 100.0})


def render_step2():
    s = st.session_state
    prev = s.decisions.get(2, {})
    step_header(2, "采购 · 选供应商")
    st.markdown("**场景**：原材料 5000 kg，需选定供应商。价格、交期、质量三者不可兼得。")
    opts = ["均衡供应商（推荐⭐）：价格12元/kg·交期5天·质量系数1.0",
            "低价供应商：价格11元/kg·质量系数0.9·返工风险高",
            "优质供应商：价格13.5元/kg·质量系数1.08·交期7天"]
    opt_key = {0: "均衡供应商", 1: "低价供应商", 2: "优质供应商"}
    prev_key = prev.get("supplier", "均衡供应商")
    idx2 = next((i for i, k in opt_key.items() if k == prev_key), 0)
    sel = st.radio("选择供应商", opts, index=idx2,
                   format_func=lambda x: x, key="s2_sup")
    sup_key = opt_key[opts.index(sel)]
    st.info(f"当前选择：**{sup_key}** — {SUPPLIERS[sup_key]['desc']}")
    finish_button(2, {"supplier": sup_key})


def render_step3():
    s = st.session_state
    prev = s.decisions.get(3, {})
    sup = SUPPLIERS.get(s.decisions.get(2, {}).get("supplier", "均衡供应商"), SUPPLIERS["均衡供应商"])
    step_header(3, "入库 · 材料单价与采购量")
    st.markdown(f"**场景**：确定入库单价与采购量（供应商基准价 {sup['price']:.1f} 元/kg）。"
                f"⚠️ 单价超过 20 元将触发红线「成本造假」；采购量影响直接材料总额。")
    price = st.slider("材料单价（元/kg）", 5.0, 25.0,
                      float(prev.get("unit_price", sup["price"])), 0.5, key="s3_price")
    qty = st.slider("采购量（kg）", 1000, 10000,
                    int(prev.get("qty", 5000)), 100, key="s3_qty")
    coef = sup["coef"]
    st.markdown(f"直接材料成本 = {price:.1f} × {qty} × 质量系数 {coef:.2f} = **{price * qty * coef:,.0f} 元**")
    if price > 20:
        st.error("⚠️ 单价超过 20 元：可能触发红线「成本造假」！")
    finish_button(3, {"unit_price": price, "qty": qty})


def render_step4():
    s = st.session_state
    prev = s.decisions.get(4, {})
    step_header(4, "领料 · 投料方式")
    st.markdown("**场景**：原材料投入方式影响月末在产品材料成本的计量。")
    opts = ["一次投入（推荐⭐）：生产开始时全部投入，材料完工程度 100%",
            "陆续投入：随生产进度陆续投入，材料完工程度按 50% 计"]
    prev_feed = prev.get("feed", "一次投入")
    sel = st.radio("选择投料方式", opts, index=(0 if prev_feed == "一次投入" else 1), key="s4_feed")
    feed = "一次投入" if "一次投入" in sel else "陆续投入"
    st.info(f"材料约当产量 = 在产品数量 × 材料完工程度（{'100%' if feed == '一次投入' else '50%'}）")
    finish_button(4, {"feed": feed})


def render_step5():
    s = st.session_state
    prev = s.decisions.get(5, {})
    step_header(5, "人工 · 工时与工资率")
    st.markdown("**场景**：本月生产耗用工时与工资率，直接人工 = 工时 × 工资率。")
    hours = st.slider("生产工时（h）", 1000, 6000, int(prev.get("hours", 2000)), 50, key="s5_hours")
    wage = st.slider("工资率（元/h）", 15.0, 35.0, float(prev.get("wage", 25.0)), 0.5, key="s5_wage")
    st.markdown(f"直接人工 = {hours} × {wage:.1f} = **{hours * wage:,.0f} 元**")
    finish_button(5, {"hours": hours, "wage": wage})


def render_step6():
    s = st.session_state
    prev = s.decisions.get(6, {})
    step_header(6, "混合成本分解")
    st.markdown("**场景**：车间电费为混合成本（固定 + 变动）。请用高低点法分解。近 6 个月数据：")
    months = [("1月", 800, 56000), ("2月", 900, 60000), ("3月", 700, 52000),
              ("4月", 1000, 64000), ("5月", 850, 58000), ("6月", 950, 62000)]
    df = pd.DataFrame(months, columns=["月份", "产量(件)", "电费(元)"])
    st.dataframe(df, width="stretch", hide_index=True)
    st.markdown("**高低点法**：变动成本率 = (最高费用 − 最低费用) ÷ (最高产量 − 最低产量)"
                " = (64000−52000) ÷ (1000−700) = **40 元/件**；固定成本 = 64000 − 40×1000 = 24000 元。")
    var_rate = st.slider("你的答案：单位变动成本（元/件）", 30.0, 50.0,
                         float(prev.get("var_rate", 40.0)), 1.0, key="s6_var")
    ok = abs(var_rate - 40.0) <= 2.0
    if not ok:
        st.warning(f"偏差超出 ±2 元/件：分解失真将导致制造费用归集偏差（+3000 元）。")
    finish_button(6, {"var_rate": var_rate, "ok": ok})


def render_step7():
    s = st.session_state
    prev = s.decisions.get(7, {})
    step_header(7, "制造费用 · 分摊基数")
    st.markdown("**场景**：本月制造费用 45000 元，需选择分摊基数将费用计入产品成本。")
    opts = ["人工工时（推荐⭐）：车间以人工操作为主，人工工时最能反映费用动因",
            "机器工时：自动化程度高时更合理，本车间自动化程度中等",
            "产量：按完工产量平均分摊，适用于单一品种稳定生产"]
    prev_base = prev.get("base", "人工工时")
    idx7 = {"人工工时": 0, "机器工时": 1, "产量": 2}.get(prev_base, 0)
    sel = st.radio("选择分摊基数", opts, index=idx7, key="s7_base")
    base = "人工工时" if "人工工时" in sel else ("机器工时" if "机器工时" in sel else "产量")
    st.info(f"当前基准：**{base}**。本车间以人工操作为主，人工工时口径最合理。")
    finish_button(7, {"base": base})


def render_step8():
    s = st.session_state
    prev = s.decisions.get(8, {})
    step_header(8, "辅助生产分配")
    st.markdown("**场景**：供电车间（6000 元）与供水车间（4000 元）费用需分配到基本生产车间与管理部门。")
    method = st.radio("分配方法", ["直接分配法（推荐⭐）：不考虑辅助车间之间交互",
                                   "交互分配法：先交互再对外分配"],
                      index=(0 if prev.get("method", "直接分配法") == "直接分配法" else 1),
                      key="s8_method")
    m = "直接分配法" if "直接分配法" in method else "交互分配法"
    pct = st.slider("供电车间分配给基本生产车间的比例（%）", 40, 80,
                    int(prev.get("pct", 60)), 5,
                    help="基准：直接分配法下供电车间 60% 给基本生产、40% 给管理部门。",
                    key="s8_pct")
    ok = m == "直接分配法" and pct == 60
    if not ok:
        st.warning("与基准分配方案不一致：辅助费用归集偏差 +2000 元。")
    st.markdown(f"供电→基本生产 {pct}%（{6000*pct/100:,.0f} 元）；供电→管理 {100-pct}%（{6000*(100-pct)/100:,.0f} 元）")
    finish_button(8, {"method": m, "pct": pct, "ok": ok})


def render_step9():
    s = st.session_state
    prev = s.decisions.get(9, {})
    step_header(9, "约当产量 · 完工程度")
    st.markdown("**场景**：本月完工 300 件，月末在产品待定。请设定在产品数量与加工完工程度。"
                "⚠️ 在产品数量超过完工数量×2 将触发红线「虚增存货」。")
    wip = st.slider("月末在产品数量（件）", 0, 900, int(prev.get("wip_qty", 100)), 10, key="s9_wip")
    pct9 = st.slider("加工完工程度（%）", 0, 100, int(prev.get("proc_pct", 50)), 5, key="s9_pct")
    st.markdown(f"加工约当产量 = {wip} × {pct9}% = **{wip * pct9 / 100:,.0f} 件**")
    if wip > 600:
        st.error("⚠️ 在产品数量超过完工数量×2（600 件）：将触发红线「虚增存货」！")
    finish_button(9, {"wip_qty": wip, "proc_pct": pct9})


def render_step10():
    s = st.session_state
    prev = s.decisions.get(10, {})
    step_header(10, "品种法 · 成本计算单")
    st.markdown("**场景**：填写品种法成本计算单。参考区间：材料单位成本 145-155 元，加工单位成本 265-278 元。")
    c1 = st.number_input("材料单位成本（元）", 0.0, 1000.0, float(prev.get("mat_unit_in", 150.0)), 1.0, key="s10_m")
    c2 = st.number_input("加工单位成本（元）", 0.0, 1000.0, float(prev.get("proc_unit_in", 271.0)), 1.0, key="s10_p")
    ok = (145 <= c1 <= 155) and (265 <= c2 <= 278)
    if not ok:
        st.warning("与参考答案范围不符：请核查材料总额口径与约当产量后再填。")
    else:
        st.success("✔ 与参考答案范围一致，单位产品成本核算准确。")
    finish_button(10, {"mat_unit_in": c1, "proc_unit_in": c2, "ok": ok})


def render_step11():
    s = st.session_state
    prev = s.decisions.get(11, {})
    step_header(11, "分批法 · 批次成本")
    st.markdown("**场景**：两个订单按批归集成本。订单A：100 件，材料 25000、人工 15000、制造 10000；"
                "订单B：80 件，材料 20000、人工 12000、制造 8000。售价均 600 元/件。")
    a = st.number_input("订单A 批次成本（元）", 0.0, 200000.0, float(prev.get("a", 50000.0)), 500.0, key="s11_a")
    b = st.number_input("订单B 批次成本（元）", 0.0, 200000.0, float(prev.get("b", 40000.0)), 500.0, key="s11_b")
    ok = abs(a - 50000) <= 2500 and abs(b - 40000) <= 2000
    if ok:
        st.success(f"✔ 批次成本准确：A 毛利 {100*600-a:,.0f} 元，B 毛利 {80*600-b:,.0f} 元。")
    else:
        st.warning("批次成本与归集结果不符：请核对订单材料/人工/制造费用归集。")
    finish_button(11, {"a": a, "b": b, "ok": ok})


def render_step12():
    s = st.session_state
    prev = s.decisions.get(12, {})
    step_header(12, "分步法 · 成本还原计算器")
    st.markdown("**场景**：逐步结转分步法下，半成品成本需还原。只需填 3 个关键数字，系统自动完成还原计算。")
    half_qty = st.number_input("半成品数量（件）", 1, 1000, int(prev.get("half_qty", 200)), 10, key="s12_q")
    half_unit = st.number_input("半成品单位成本（元）", 0.0, 2000.0, float(prev.get("half_unit", 350.0)), 10.0, key="s12_u")
    reduce_rate = st.number_input("材料还原率（%）", 0, 100, int(prev.get("reduce_rate", 60)), 5, key="s12_r")
    mat_red = half_qty * half_unit * reduce_rate / 100.0
    proc_red = half_qty * half_unit * (100 - reduce_rate) / 100.0
    unit_red = half_qty * half_unit / half_qty
    st.markdown(f"**还原结果**：直接材料 {mat_red:,.0f} 元 / 加工成本 {proc_red:,.0f} 元 → "
                f"还原后单位成本 **{unit_red:,.0f} 元/件**")
    ok = abs(reduce_rate - 60) <= 5 and abs(half_unit - 350) <= 20 and half_qty == 200
    if not ok:
        st.warning("与参考答案（200 件 / 350 元 / 60%）存在偏差，注意半成品成本构成口径。")
    finish_button(12, {"half_qty": half_qty, "half_unit": half_unit,
                       "reduce_rate": reduce_rate, "ok": ok})


def render_step13():
    s = st.session_state
    prev = s.decisions.get(13, {})
    step_header(13, "两法切换 · 变动/完全成本法")
    st.markdown("**场景**：选择成本核算口径。完全成本法将固定制造费用计入存货（库存吸收），"
                "变动成本法则全额当期损益化。")
    opts = ["完全成本法（推荐⭐）：单位成本含固定制造费用，存货吸收固定成本",
            "变动成本法：固定制造费用全额计入当期损益，利润更贴近现金流"]
    prev_method = prev.get("cost_method", "完全成本法")
    sel = st.radio("选择成本法", opts, index=(0 if prev_method == "完全成本法" else 1), key="s13_m")
    method = "完全成本法" if "完全成本法" in sel else "变动成本法"
    st.info("完全成本法下：利润 = 售价×销量 − 单位成本×销量；变动成本法下：利润 = (售价−单位变动)×销量 − 固定制造费用。")
    finish_button(13, {"cost_method": method})


def render_step14():
    s = st.session_state
    prev = s.decisions.get(14, {})
    step_header(14, "量本利分析")
    st.markdown("**场景**：调整单价、销量与变动成本率，观察保本点与经营利润。"
                "（若已进入步15，产销情境将覆盖销量设置）")
    price = st.slider("产品单价（元）", 200, 1000, int(prev.get("price", 600)), 10, key="s14_price")
    sales_qty = st.slider("销量（件）", 100, 500, int(prev.get("sales_qty", 300)), 10, key="s14_sales")
    var_ratio = st.slider("变动成本率（%）", 40, 80, int(prev.get("var_ratio", 60)), 1,
                          help="材料+人工占收入比例，用于量本利演示", key="s14_var")
    unit_var = price * var_ratio / 100.0
    fixed = 45000.0
    bep = fixed / max(1e-6, price - unit_var)
    profit = (price - unit_var) * sales_qty - fixed
    st.markdown(f"**保本点 = {bep:,.0f} 件**（当前销量 {sales_qty} 件） · "
                f"本量利口径利润 = **{profit:,.0f} 元**")
    if sales_qty < bep:
        st.warning("当前销量低于保本点，处于亏损区间！")
    finish_button(14, {"price": float(price), "sales_qty": int(sales_qty),
                       "var_ratio": int(var_ratio)})


def render_step15():
    s = st.session_state
    prev = s.decisions.get(15, {})
    step_header(15, "产销情境")
    st.markdown("**场景**：选择本期产销结构，影响期末存货与利润口径（产量 300 件）。")
    opts = ["产销平衡（推荐⭐）：产量=销量=300 件，无存货吸收效应",
            "存货增加：销量 250 件，期末存货 50 件（完全成本法下吸收固定成本，利润更高）",
            "销售下滑：销量 200 件，期末存货 100 件"]
    prev_scen = prev.get("scenario", "产销平衡")
    idx15 = {"产销平衡": 0, "存货增加": 1, "销售下滑": 2}.get(prev_scen, 0)
    sel = st.radio("选择产销情境", opts, index=idx15, key="s15_scen")
    scen = "产销平衡" if "产销平衡" in sel else ("存货增加" if "存货增加" in sel else "销售下滑")
    st.info(f"情境：**{scen}**（销量={'300' if scen == '产销平衡' else ('250' if scen == '存货增加' else '200')} 件）")
    finish_button(15, {"scenario": scen})


def render_step16():
    s = st.session_state
    prev = s.decisions.get(16, {})
    step_header(16, "存货计价")
    st.markdown("**场景**：选择发出存货计价方法。在价格上升假设下，先进先出使已销成本偏低、利润偏高。")
    opts = ["先进先出（FIFO，推荐⭐）：已销成本偏低，当期利润相对较高",
            "加权平均：已销成本居中，利润平稳",
            "个别计价：按实际批次结转，已销成本偏高，利润相对较低"]
    prev_inv = prev.get("inv_method", "先进先出")
    idx16 = {"先进先出": 0, "加权平均": 1, "个别计价": 2}.get(prev_inv, 0)
    sel = st.radio("选择存货计价方法", opts, index=idx16, key="s16_inv")
    inv = "先进先出" if "先进先出" in sel else ("加权平均" if "加权平均" in sel else "个别计价")
    finish_button(16, {"inv_method": inv})


def render_step17():
    s = st.session_state
    prev = s.decisions.get(17, {})
    step_header(17, "标准成本设定")
    st.markdown("**场景**：设定标准料工费，系统将据此计算标准单位成本与成本偏离指数。"
                "默认标准使正常场景落于绿色区间（95-105%）。")
    p1 = st.slider("标准材料单价（元/kg）", 8.0, 16.0, float(prev.get("std_mat_price", 12.0)), 0.5, key="s17_p1")
    p2 = st.slider("标准采购量（kg）", 4000, 6000, int(prev.get("std_mat_qty", 5000)), 100, key="s17_p2")
    p3 = st.slider("标准工时（h）", 1600, 2400, int(prev.get("std_hours", 2000)), 50, key="s17_p3")
    p4 = st.slider("标准工资率（元/h）", 22.0, 32.0, float(prev.get("std_wage", 27.0)), 0.5, key="s17_p4")
    p5 = st.slider("标准制造费用（元）", 35000, 55000, int(prev.get("std_overhead", 40500)), 500, key="s17_p5")
    std_mat = p1 * p2
    std_proc = p3 * p4 + p5
    cfg = get_cfg()
    r = engine_calc(std_mat, std_proc, cfg["finished_qty"], cfg["wip_qty"],
                    cfg["mat_pct"], cfg["proc_pct"])
    st.markdown(f"标准材料总额 {std_mat:,.0f} 元，标准加工总额 {std_proc:,.0f} 元 → "
                f"**标准单位成本 = {r['unit_cost']:,.2f} 元/件**")
    finish_button(17, {"std_mat_price": p1, "std_mat_qty": p2, "std_hours": p3,
                       "std_wage": p4, "std_overhead": p5})


def render_step18():
    s = st.session_state
    prev = s.decisions.get(18, {})
    step_header(18, "差异分析 · 责任归属")
    st.markdown("**场景**：把三类成本差异归属到正确的责任中心。选错会放大责任中心超支记录。")
    o1_opts = ["采购中心（推荐⭐）：采购价格超支由采购环节负责", "生产中心", "销售部"]
    o2_opts = ["生产中心（推荐⭐）：材料超耗由生产环节负责", "采购中心", "财务部"]
    o3_opts = ["车间班组（推荐⭐）：工时效率由一线班组负责", "采购中心", "管理层"]
    idx18 = lambda opts, v: opts.index(v) if v in opts else 0
    o1 = st.radio("价格差异 →", o1_opts, index=idx18(o1_opts, prev.get("o1")), key="s18_o1")
    o2 = st.radio("用量差异 →", o2_opts, index=idx18(o2_opts, prev.get("o2")), key="s18_o2")
    o3 = st.radio("效率差异 →", o3_opts, index=idx18(o3_opts, prev.get("o3")), key="s18_o3")
    ok = ("采购中心" in o1) and ("生产中心" in o2) and ("车间班组" in o3)
    if ok:
        st.success("✔ 三类差异均归属正确，责任中心记录清晰。")
    else:
        st.warning("存在差异归属错误：责任中心超支记录将被放大。")
    finish_button(18, {"o1": o1, "o2": o2, "o3": o3, "ok": ok})


def render_step19():
    s = st.session_state
    prev = s.decisions.get(19, {})
    step_header(19, "金点子 · 降本增效方案")
    st.markdown("**场景**：撰写一条降本增效方案（100-300 字），AI 将按"
                "**创新性30% + 可操作性30% + 成本影响25% + 业财融合15%** 评判（0-100 分）。")
    idea = st.text_area("降本增效方案", value=prev.get("idea", ""),
                        height=160, placeholder="例如：引入能耗数字化监控，按班组核算电费并纳入月度绩效，预计月节约 1.2 万元……",
                        key="s19_idea")
    st.caption("提示：包含具体措施、实施步骤、成本节约金额与责任指标，可获得更高评分。提交后由本地规则引擎即时判分（无需等待）。")
    if st.button("🤖 提交方案并判分", type="primary", key="s19_btn"):
        if len(idea.strip()) < 12:
            st.error("方案过短（少于 12 字），请补充后再提交。")
            return
        score, comment, dims = ai_score_idea(idea)
        st.session_state.decisions[19] = {"idea": idea, "ai_score": score,
                                          "ai_comment": comment, "dims": dims}
        st.session_state.step_ok[19] = True
        finalize(19)
        st.session_state.current_step = 20
        st.rerun()
    if prev.get("ai_score") is not None:
        st.success(f"AI 评分：**{prev['ai_score']:.1f} / 100** —— {prev['ai_comment']}")


def render_step20():
    s = st.session_state
    prev = s.decisions.get(20, {})
    step_header(20, "作业成本法 · 动因选择")
    st.markdown("**场景**：选择资源动因与作业动因，使间接费用重摊更贴近真实成本动因。")
    r1_opts = ["机器工时（推荐⭐）：电费随机器运转消耗", "人工工时", "产量"]
    r2_opts = ["检验批次（推荐⭐）：质检费随检验批次发生", "产量", "机器工时"]
    idx20 = lambda opts, v: opts.index(v) if v in opts else 0
    r1 = st.radio("资源动因 → 电费", r1_opts, index=idx20(r1_opts, prev.get("r1")), key="s20_r1")
    r2 = st.radio("作业动因 → 质检费用", r2_opts, index=idx20(r2_opts, prev.get("r2")), key="s20_r2")
    ok = ("机器工时" in r1) and ("检验批次" in r2)
    if not ok:
        st.warning("动因选择与作业特性不匹配：间接费用重摊失真，制造费用上浮 4%。")
    finish_button(20, {"r1": r1, "r2": r2, "ok": ok})


def render_step21():
    s = st.session_state
    prev = s.decisions.get(21, {})
    step_header(21, "动因博弈")
    st.markdown("**场景**：AI 提示：'检验次数'动因与质检成本弱相关（r=0.3），"
                "是否改用'批次'作为作业动因？改用可提升核算精度，但短期需投入改造。")
    opts = ["改（推荐⭐）：核算精度提升，制造费用 +2%（短期投入）",
            "不改：短期利润保持，但核算精度下降"]
    prev_choice = prev.get("choice", "改")
    sel = st.radio("你的决策", opts, index=(0 if prev_choice == "改" else 1), key="s21_ch")
    choice = "改" if "改" in sel else "不改"
    finish_button(21, {"choice": choice})


def render_step22():
    s = st.session_state
    prev = s.decisions.get(22, {})
    step_header(22, "责任中心划分")
    st.markdown("**场景**：把下列单元划入成本中心/利润中心。⚠️ 选择'全部推给他方'将触发红线「责任甩锅」。")
    opts = ["生产车间→成本中心，销售部→利润中心（推荐⭐）：按可控性划分",
            "生产车间→利润中心，销售部→成本中心：职责错配，考核失真",
            "全部推给他方：把责任全部推给外部/其他部门（触发红线）"]
    prev_cc = prev.get("center_choice", "生产车间→成本中心，销售部→利润中心")
    idx22 = {"生产车间→成本中心，销售部→利润中心": 0,
             "生产车间→利润中心，销售部→成本中心": 1,
             "全部推给他方": 2}.get(prev_cc, 0)
    sel = st.radio("责任中心划分", opts, index=idx22, key="s22_cc")
    cc = "生产车间→成本中心，销售部→利润中心" if "生产车间→成本中心" in sel else \
        ("生产车间→利润中心，销售部→成本中心" if "利润中心" in sel else "全部推给他方")
    if cc == "全部推给他方":
        st.error("⚠️ 该选择将触发红线「责任甩锅」！")
    finish_button(22, {"center_choice": cc})


def render_step23():
    s = st.session_state
    step_header(23, "数据仪表盘")
    st.markdown("**场景**：综合查看成本结构、利润趋势与成本偏离情况（本步无操作，仅观察）。")
    cfg = get_cfg()
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_cost_pie(cfg), width="stretch")
    with c2:
        st.plotly_chart(plot_profit_line(s.history), width="stretch")
    st.plotly_chart(plot_deviation_bar(s.history), width="stretch")
    if st.button("✅ 我已查看仪表盘，进入下一步", type="primary", key="s23_btn"):
        finish_button_go(23, {"viewed": True})


def finish_button_go(no, decision, ok=None):
    s = st.session_state
    s.decisions[no] = decision
    if ok is not None:
        s.step_ok[no] = ok
    finalize(no)
    if no < STEP_FULL:
        s.current_step = no + 1
    else:
        s.current_step = STEP_FULL
    st.rerun()


def board_finish(no, decision, ok=None):
    """独立板块完成：记账但不推进主线 current_step"""
    s = st.session_state
    s.decisions[no] = decision
    if ok is not None:
        s.step_ok[no] = ok
    finalize(no)
    st.rerun()


def render_step24():
    s = st.session_state
    prev = s.decisions.get(24, {})
    if s.risk_event_id is None:
        import random
        s.risk_event_id = random.choice(risk_events_pool())["id"]
    event = next(e for e in risk_events_pool() if e["id"] == s.risk_event_id)
    step_header(24, "风险事件应对")
    st.markdown(f"**{event['name']}**\n\n{event['desc']}")
    opts = [f"{o['label']}：{o['desc']}" for o in event["options"]]
    idx24 = next((i for i, o in enumerate(event["options"]) if o["label"] == prev.get("choice")), 0)
    sel = st.radio("应对决策", opts, index=idx24, key="s24_sel")
    idx = opts.index(sel)
    opt = event["options"][idx]
    # 真正的二次确认：确认键随（事件+当前选项）变化，改选项或离开即复位
    if s.get("step24_confirm_key") != (s.risk_event_id, sel):
        s.step24_confirm = False
        s.step24_confirm_key = (s.risk_event_id, sel)
    st.warning("该决策将影响后续成本与利润，且不可反悔。请二次确认。")
    if not s.step24_confirm:
        if st.button("⚠️ 确认该决策（一次确认）", type="primary", key="s24_btn"):
            s.step24_confirm = True
            st.rerun()
    else:
        st.error(f"即将执行：**{opt['label']}** —— 请最后确认")
        if st.button("🚫 再次确认执行（不可撤销）", type="primary", key="s24_btn2"):
            fx = dict(opt["fx"])
            q = opt["q"]
            s.step24_confirm = False
            s.step24_confirm_key = None
            finish_button_go(24, {"event_id": event["id"], "choice": opt["label"],
                                  "fx": fx, "choice_quality": q})
    if prev.get("choice"):
        st.success(f"已应对：**{prev['choice']}**")


def render_step25():
    s = st.session_state
    step_header(25, "红线检查")
    st.markdown("**系统判定**：以下红线按两次触发制检查（第一次警告+扣30分，第二次实验终止）。")
    cfg = get_cfg()
    lines = red_line_status(cfg, s.decisions)
    rows = []
    for ln in RED_LINE_NAMES:
        rows.append({"红线": ln, "触发条件": {"成本造假": "材料单价 > 20 元",
                                           "虚增存货": "在产品 > 完工 × 2",
                                           "责任甩锅": "责任中心全推他人"}[ln],
                     "当前状态": "⚠️ 触发" if ln in lines else "✔ 未触发",
                     "累计触碰": f"{s.red_lines[ln]} 次"})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    if s.terminated:
        st.error("实验已因第二次触碰红线而终止！请重新开始。")
    else:
        st.success("红线检查通过（或仅首次警告）：可继续。")
        if st.button("✅ 确认检查结果，进入下一步", type="primary", key="s25_btn"):
            finish_button_go(25, {"checked": True})


def render_step26():
    s = st.session_state
    prev = s.decisions.get(26, {})
    st.subheader("📋 同口径复盘")
    st.caption("独立板块 · 对比本轮与上一轮实验的同口径指标，识别改进点")
    cur = s.indicators
    if cur is None:
        st.info("尚未完成任何步骤，无可复盘数据。")
        return
    prev_round = getattr(s, "past_rounds", None)
    if prev_round:
        p = prev_round[-1]
        df = pd.DataFrame([
            {"指标": "单位产品成本（元）", "上轮": f"{p['unit_cost']:,.2f}", "本轮": f"{cur['unit_cost']:,.2f}"},
            {"指标": "经营利润（元）", "上轮": f"{p['profit']:,.0f}", "本轮": f"{cur['profit']:,.0f}"},
            {"指标": "成本偏离指数", "上轮": f"{p['deviation']:.1f}%", "本轮": f"{cur['deviation']:.1f}%"},
            {"指标": "责任绩效分", "上轮": f"{p['perf']:.1f}", "本轮": f"{cur['perf']:.1f}"},
        ])
        st.dataframe(df, width="stretch", hide_index=True)
        adv = []
        if cur["deviation"] < p["deviation"]:
            adv.append("本轮成本偏离改善，继续保持材料与制造费用控制。")
        if cur["profit"] > p["profit"]:
            adv.append("本轮利润提升，产销与定价策略有效。")
        if cur["perf"] > p["perf"]:
            adv.append("责任绩效改善，差异归属与责任划分更到位。")
        if not adv:
            adv.append("与上轮持平：可在金点子与经营决策报告中寻求突破。")
        st.info("改进建议：" + " ".join(adv))
    else:
        # 首轮实验：展示本轮各步骤四指标演化明细，作为下次复盘的基准
        if s.history:
            df2 = pd.DataFrame([{
                "步骤": h["step"],
                "单位成本（元）": f"{h['unit_cost']:,.2f}",
                "经营利润（元）": f"{h['profit']:,.0f}",
                "偏离指数（%）": f"{h['deviation']:.1f}",
                "绩效分": f"{h['perf']:.1f}"} for h in s.history])
            st.dataframe(df2, width="stretch", hide_index=True)
        st.info("本轮为第 1 轮实验：暂无上轮对比数据，以上为本轮各步骤指标演化；完成后再开新轮次，即可在同口径下做两轮对比。")
    if st.button("✅ 确认复盘完成", type="primary", key="s26_btn"):
        board_finish(26, {"reviewed": True})


def render_step27():
    s = st.session_state
    prev = s.decisions.get(27, {})
    st.subheader("🛡️ 能力画像 · 五维雷达")
    st.caption("独立板块 · 系统根据你的过程表现生成五维能力画像（终结性评价依据）")
    compute_scores()
    st.plotly_chart(plot_radar(s.scores), width="stretch")
    st.caption("维度说明：核算准确（步10/11/12）· 成本分析（步6/8/14/17）· 决策能力（步15/21/24）· "
               "业财融合（步13/16/20/22）· 创新意识（步19）")
    if st.button("✅ 确认已查看画像", type="primary", key="s27_btn"):
        board_finish(27, {"captured": True})


def build_report():
    s = st.session_state
    ind = s.indicators or {}
    lines = []
    lines.append("=" * 46)
    lines.append("智控成本 · 数创价值 —— 经营决策报告书")
    lines.append("=" * 46)
    lines.append(f"版本：{APP_VERSION} · 生成时间：{time.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("一、核心指标")
    lines.append(f"  单位产品成本：{ind.get('unit_cost', 0):,.2f} 元/件")
    lines.append(f"  经营利润：{ind.get('profit', 0):,.0f} 元")
    lines.append(f"  成本偏离指数：{ind.get('deviation', 0):.1f}%（{ind.get('deviation_color', '绿')}）")
    lines.append(f"  责任绩效分：{ind.get('perf', 0):.1f} / 100")
    lines.append(f"  已用时长：{int(time.time() - s.start_time)} 秒")
    lines.append("")
    lines.append("二、定价建议")
    dev = ind.get("deviation", 100)
    if dev > 105:
        lines.append("  成本偏离偏高：建议将售价上调至覆盖成本，或通过步3/步7/步8压缩材料与制造费用。")
    elif ind.get("profit", 0) < 0:
        lines.append("  当前亏损：优先提高售价或降低变动成本，恢复正向利润后再谈扩张。")
    else:
        lines.append("  成本可控：可维持当前定价，并考虑按目标利润率（"
                     + f"{s.decisions.get(1, {}).get('target_margin', 0.15)*100:.0f}%）检核加价空间。")
    lines.append("")
    lines.append("三、排产建议")
    d15 = s.decisions.get(15, {}).get("scenario", "产销平衡")
    if d15 == "销售下滑":
        lines.append("  销量下滑：建议收缩排产至与销量匹配，减少存货积压与资金占用。")
    elif d15 == "存货增加":
        lines.append("  存货增加：注意消化库存，避免完全成本法下存货吸收掩盖真实盈利。")
    else:
        lines.append("  产销平衡：维持当前排产节奏，聚焦良率与效率提升。")
    lines.append("")
    lines.append("四、考核建议")
    perf = ind.get("perf", 0)
    if perf >= 85:
        lines.append("  责任绩效优秀：可晋升为成本管控标杆岗位。")
    elif perf >= 60:
        lines.append("  责任绩效良好：建议强化差异分析与责任中心考核。")
    else:
        lines.append("  责任绩效待提升：需重点整改红线风险与责任划分。")
    strikes = [ln for ln, c in s.red_lines.items() if c > 0]
    if strikes:
        lines.append(f"  红线记录：{'、'.join(strikes)}（触碰 {sum(s.red_lines.values())} 次，已扣分）")
    lines.append("")
    lines.append("五、终结性评分")
    score = final_score()
    lines.append(f"  综合评分：{score:.1f} / 100")
    lines.append(f"  能力画像：{', '.join(f'{k} {v:.0f}' for k, v in s.scores.items())}")
    lines.append("")
    lines.append("（本报告由系统按过程数据自动生成，供课程考核与复盘使用。）")
    return "\n".join(lines)


def final_score():
    s = st.session_state
    ind = s.indicators or {}
    perf = ind.get("perf", 0)
    idea = s.decisions.get(19, {}).get("ai_score", 0)
    quality = s.scores.get("决策能力", 40)
    score = min(100.0, 0.60 * perf + 0.20 * idea + 0.10 * quality
                + (10.0 if s.decisions.get(18, {}).get("ok") else 0.0))
    return score


def render_step28():
    s = st.session_state
    st.subheader("📊 经营决策报告")
    st.caption("独立板块 · 基于全程数据生成定价、排产、考核建议书与终结性评分")
    report = build_report()
    st.text(report)
    st.download_button("📥 下载报告（TXT）", report,
                       file_name=f"成本决策报告_{time.strftime('%Y%m%d_%H%M')}.txt",
                       mime="text/plain", key="s28_dl")
    if s.final_report is None:
        s.final_report = report
    st.success(f"实验完成！综合评分 **{final_score():.1f} / 100**。可回到任意已完成步骤复查，或重新开始。")
    if st.button("✅ 确认完成（实验结束）", type="primary", key="s28_btn"):
        board_finish(28, {"report_done": True, "report": report})


# ============================================================================
# 六、全局组件（导航 / 指标面板 / 词条 / 教师模式）
# ============================================================================
def _nav_side_cb(mod_id):
    """侧边栏步骤导航 on_change 回调：回看已完成步骤 / 26-28 切板块"""
    sel = st.session_state.get(f"nav_pills_{mod_id}")
    if not sel:
        return
    no = int(sel.split(" ")[0])
    s = st.session_state
    last = s.get(f"_nav_last_{mod_id}")
    if no in s.decisions or no == s.current_step:
        if last != no:
            s[f"_nav_last_{mod_id}"] = no
            if no != s.current_step:
                if no >= 26:
                    _nav_cb({26: "复盘", 27: "画像", 28: "报告"}[no])
                else:
                    s.current_step = no
    elif last != -no:
        s[f"_nav_last_{mod_id}"] = -no
        st.sidebar.toast(f"第 {no} 步尚未完成，请按顺序完成前面的步骤后再跳转")


def render_sidebar():
    s = st.session_state
    st.sidebar.markdown("### 🎯 智控成本 · 数创价值")
    st.sidebar.caption("选择决策并完成 25 步决策主线 · 四指标实时刷新")
    st.sidebar.markdown("## 🎯 四指标实时面板")
    ind = s.indicators
    if ind is None:
        st.sidebar.info("完成第 1 步后开始实时刷新")
    else:
        dev_color = {"蓝": "#1E88E5", "绿": "#00A86B", "黄": "#F9A825", "红": "#E53935"}[ind["deviation_color"]]
        st.sidebar.metric("单位产品成本", f"{ind['unit_cost']:,.2f} 元")
        st.sidebar.metric("经营利润", f"{ind['profit']:,.0f} 元",
                          delta=f"{ind['profit']:,.0f}", delta_color="normal")
        st.sidebar.markdown(f"**成本偏离指数**：{ind['deviation']:.1f}% "
                            f"<span style='color:{dev_color}'>● {ind['deviation_color']}</span>",
                            unsafe_allow_html=True)
        st.sidebar.metric("责任绩效分", f"{ind['perf']:.1f} / 100")
    completed = sum(1 for i in range(1, MAIN_FULL + 1) if i in s.decisions)
    st.sidebar.progress(completed / MAIN_FULL)
    st.sidebar.caption(f"已完成 {completed} / {MAIN_FULL} · 当前第 {s.current_step} 步")
    elapsed = int(time.time() - s.start_time)
    remain = int(elapsed / max(1, completed) * (MAIN_FULL - completed)) if completed else 0
    st.sidebar.caption(f"已用 {elapsed // 60} 分 {elapsed % 60} 秒 · 预计剩余约 {remain // 60} 分")
    # 红线状态
    with st.sidebar.expander("🚨 红线状态", expanded=False):
        for ln in RED_LINE_NAMES:
            c = s.red_lines[ln]
            mark = "⚠️" if c > 0 else "✔"
            st.markdown(f"{mark} {ln}：累计触碰 {c} 次")
        if s.terminated:
            st.error("实验已终止")
    # 悔棋
    if st.sidebar.button(f"↩️ 悔棋（剩余 {s.undo_left} 次，回退前5步）", key="undo_btn",
                         disabled=s.undo_left <= 0 or s.current_step <= 2 or s.terminated):
        if undo():
            st.rerun()
        else:
            st.sidebar.warning("暂无可回退的步骤")
    # 模块导航：三模块色条 + pills 短标签（简短好看）+ 彩色状态提醒
    st.sidebar.markdown("### 🧭 步骤导航")
    st.sidebar.caption("点已完成步骤可回看 · 未完成步骤按顺序走")
    # 25 步彩色状态点阵（仅决策台主线）：绿=已完成 / 蓝=当前 / 灰=未完成（悬停显示步骤名）
    dot_html = []
    for no, name, _, _, _ in MAIN_STEPS:
        if no in s.decisions:
            color, mark, tip = "#2e9e5b", "✓", f"已完成 · {no}. {name}"
        elif no == s.current_step:
            color, mark, tip = "#1f6feb", "➤", f"当前步骤 · {no}. {name}"
        else:
            color, mark, tip = "#c6d2e2", "", f"未完成 · {no}. {name}"
        dot_html.append(
            f'<span title="{tip}" style="display:inline-block;width:13px;height:13px;margin:1px;'
            f'border-radius:3px;background:{color};color:#fff;font-size:9px;line-height:13px;'
            f'text-align:center">{mark}</span>')
    st.sidebar.markdown(
        f'<div style="margin:4px 0 2px" title="绿=已完成 · 蓝=当前 · 灰=未完成">{"".join(dot_html)}</div>',
        unsafe_allow_html=True)
    for mod_id, mod_name, _ in MODULES:
        steps_in_mod = [s0 for s0 in MAIN_STEPS if s0[2] == mod_id]
        accent = MODULE_ACCENTS[mod_id]
        done_in_mod = sum(1 for no, _, m, _, _ in MAIN_STEPS if m == mod_id and no in s.decisions)
        st.sidebar.markdown(
            f"<div style='border-left:4px solid {accent};padding:2px 8px;margin:8px 0 2px;"
            f"font-weight:700;color:{accent};font-size:13px'>{mod_name}"
            f"<span style='float:right;color:#9aa7bd;font-weight:400;font-size:12px'>"
            f"已完成 {done_in_mod}/{len(steps_in_mod)}</span></div>",
            unsafe_allow_html=True)
        labels = [f"{no} {NAV_SHORT[no]}" for no, _, _, _, _ in steps_in_mod]
        st.sidebar.pills("跳转", labels, key=f"nav_pills_{mod_id}",
                         selection_mode="single", label_visibility="collapsed",
                         on_change=_nav_side_cb, args=(mod_id,))
    # 教师模式
    teacher = st.sidebar.checkbox("👩‍🏫 教师模式", key="teacher_mode")
    if teacher:
        st.sidebar.markdown("### 成绩汇总")
        st.sidebar.caption(f"综合评分：{final_score():.1f} / 100")
        df = pd.DataFrame([
            {"步骤": i, "名称": name, "完成": "✔" if i in s.decisions else "—"}
            for i, name, _, _, _ in MAIN_STEPS])
        st.sidebar.dataframe(df, width="stretch", hide_index=True)
        if s.decisions:
            dec_rows = [{"步骤": k, "决策": str(v)[:120]} for k, v in sorted(s.decisions.items())]
            csv = pd.DataFrame(dec_rows).to_csv(index=False).encode("utf-8-sig")
            st.sidebar.download_button("📊 导出决策明细 CSV", csv, "决策明细.csv",
                                       "text/csv", key="teacher_csv")
    if st.sidebar.button("🔄 重新开始", key="restart_btn"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


def render_landing():
    """着陆页：参照《数据资产运营总监》版面——渐变标题块 + 实验地图 + 逻辑主线 + 实训节奏 + 实验介绍"""
    s = st.session_state
    st.markdown(
        '<div style="background:linear-gradient(135deg,#0b3d91 0%,#1f6feb 55%,#2e9e5b 130%);'
        'padding:34px 30px;border-radius:16px;color:#fff;margin-bottom:12px;'
        'box-shadow:0 10px 30px rgba(11,61,145,0.25);'
        'border-bottom:4px solid rgba(255,255,255,0.25)">'
        '<div style="font-size:34px;font-weight:700;letter-spacing:1.5px">🎯 智控成本 · 数创价值</div>'
        '<div style="font-size:15px;opacity:0.92;margin-top:10px;line-height:1.7">'
        '制造企业全流程成本管理虚拟仿真决策实训 · 西南财经大学天府学院《成本管理会计 ACT1415A》课程组 · '
        f'{APP_VERSION} · 3 学时（每模块 1 课时）</div></div>',
        unsafe_allow_html=True)

    st.markdown("## 🗺️ 实验地图：25 步决策主线 + 3 大输出板块（从上到下依次完成）")
    map_items = [
        ("模块A · 成本核算基本功", "步骤 1-10", "#0b3d91",
         "把成本算对——材料采购、费用归集、约当产量与品种法成本计算单，打牢核算底子"),
        ("模块B · 两法对比与决策", "步骤 11-19", "#1f6feb",
         "把差异说清——分批/分步法、变动与完全成本法对比、量本利与标准成本差异，方法决定口径"),
        ("模块C · 作业责任与降本", "步骤 20-25", "#2e9e5b",
         "把降本做实——作业成本、责任中心、风险与红线；主线收官后在复盘/画像/报告三大板块完成闭环输出"),
    ]
    c1, c2, c3 = st.columns(3)
    for col, (title, span, accent, desc) in zip((c1, c2, c3), map_items):
        with col:
            st.markdown(
                f'<div style="border:1px solid #dbe4f5;border-top:5px solid {accent};'
                'border-radius:10px;padding:14px 14px;min-height:158px;background:#f8fafd">'
                f'<div style="font-weight:700;font-size:16px;color:#0b3d91">{title}</div>'
                f'<div style="font-size:13px;color:#666;margin:4px 0 8px">{span}</div>'
                f'<div style="font-size:14px;color:#333;line-height:1.6">{desc}</div></div>',
                unsafe_allow_html=True)

    st.markdown("💡 **逻辑主线**：先把成本算对、把家底摸清（模块A），再用两法对比与差异诊断看清利润背后的口径（模块B），"
                "最后用作业成本、责任考核把降本落到责任人头上（模块C）。前 19 步决定四指标的底子，后 6 步决定责任与绩效——"
                "主线收官后，进入复盘报告 / 能力画像 / 经营决策报告三大输出板块，完成“能算对成本、解释差异、用成本做决策”的完整闭环。")

    st.markdown("## 🔄 实训节奏（为什么分三模块？）")
    rhythm = [
        ("第 1 阶段 · 把账算对",
         "材料—人工—制造费用全链路归集，约当产量法算准完工与在产品成本——先尝到甜头，建立信心"),
        ("第 2 阶段 · 把差异说清",
         "两法对比、量本利与产销情境、标准成本差异归属——制造挫败感，暴露“方法选错就亏”的认知误区"),
        ("第 3 阶段 · 把降本做实",
         "作业成本、责任中心、风险与红线——责任与风险意识决定最终绩效；主线收官后进入复盘/画像/报告三大输出板块"),
    ]
    r1, r2, r3 = st.columns(3)
    for col, (title, desc) in zip((r1, r2, r3), rhythm):
        with col:
            st.markdown(
                f'<div style="border:1px solid #e3e8f2;border-radius:10px;padding:12px 14px;'
                'height:118px;background:#ffffff">'
                f'<div style="font-weight:700;font-size:15px;color:#0b3d91">{title}</div>'
                f'<div style="font-size:13.5px;color:#444;line-height:1.6;margin-top:6px">{desc}</div></div>',
                unsafe_allow_html=True)

    with st.expander("📖 实验介绍（教学目标 · 原理 · 过程与方法）", expanded=False):
        st.markdown("**🎯 实验教学目标（学完能干什么）**\n\n"
                    "学生以“成本会计→车间核算员→财务经理→管理会计师”身份，在参数化制造工厂中把"
                    "“材料采购—领料—费用归集—产品核算—两法对比—标准/作业/责任成本—经营决策”全链路跑通，"
                    "最终能**算对成本、解释差异、用成本做决策**。")
        st.markdown("**⚙️ 实验原理**\n\n"
                    "以“单位成本—经营利润—成本偏离指数—责任绩效分”四指标为主线，每步决策实时重算；"
                    "红线机制（成本造假/虚增存货/责任甩锅，两次触发制）+ 5 类风险事件随机触发 + AI 金点子评判"
                    "（创新 30% · 可操作 30% · 成本影响 25% · 业财融合 15%）。")
        st.markdown("**🧭 过程与方法**\n\n"
                    "25 步决策主线分三模块循序渐进：卡片式决策、滑块参数；主线收官后进入复盘报告/能力画像/经营决策报告"
                    "三大独立输出板块，形成“课前预热—课中实训—课后复盘”闭环。3 次悔棋可回退前 5 步，"
                    "除红线检查外均可返回修改。")

    st.divider()
    left, center, right = st.columns([1, 2, 1])
    center.button("🚀 开始实验（进入第 1 步）", type="primary", key="start_btn",
                  width="stretch", on_click=_nav_cb, args=("决策台",))


def inject_css():
    """全局 UI 主题：浅蓝渐变背景 + 卡片化 + 统一圆角阴影，让界面清爽独特"""
    st.markdown("""<style>
    /* ===== 应用背景与主容器 ===== */
    [data-testid="stAppViewContainer"] > .main {
        background: linear-gradient(165deg, #eef3ff 0%, #f7faff 45%, #ffffff 100%);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f2f6ff 0%, #ffffff 100%);
        border-right: 1px solid #e3e9f7;
    }
    [data-testid="stSidebar"] .stMarkdown p { color: #26334d; }

    /* ===== 标题 ===== */
    h1, h2, h3 { color: #0b3d91; letter-spacing: 0.3px; }
    h1 { background: linear-gradient(90deg, #0b3d91, #1f6feb); -webkit-background-clip: text;
         -webkit-text-fill-color: transparent; }
    h2 { border-left: 5px solid #1f6feb; padding-left: 12px; }

    /* ===== 指标卡 ===== */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e3e9f7;
        border-radius: 12px;
        padding: 10px 14px;
        box-shadow: 0 2px 8px rgba(15, 40, 90, 0.06);
    }
    [data-testid="stMetricLabel"] p { color: #64748b; font-size: 13px; }
    [data-testid="stMetricValue"] { color: #0b3d91; }

    /* ===== 按钮 ===== */
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid #dbe4f5;
        box-shadow: 0 2px 6px rgba(15, 40, 90, 0.08);
        transition: all 0.15s ease;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(31, 111, 235, 0.22); }
    .stButton > button[kind="primary"] {
        background: linear-gradient(120deg, #0b3d91, #1f6feb);
        border: none; color: #fff; font-weight: 600;
    }

    /* ===== 数据表 ===== */
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden;
        border: 1px solid #e3e9f7; box-shadow: 0 2px 8px rgba(15, 40, 90, 0.05); }

    /* ===== 折叠区（词条/计算器） ===== */
    [data-testid="stExpander"] {
        border: 1px solid #e3e9f7; border-radius: 12px;
        box-shadow: 0 1px 5px rgba(15, 40, 90, 0.05); margin-bottom: 10px;
    }

    /* ===== 输入控件 ===== */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox > div > div {
        border-radius: 10px !important; border-color: #dbe4f5 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #1f6feb !important; box-shadow: 0 0 0 2px rgba(31, 111, 235, 0.15) !important;
    }

    /* ===== 进度条 ===== */
    [data-testid="stProgress"] > div > div > div { background: linear-gradient(90deg, #2e9e5b, #1f6feb); }

    /* ===== 滚动条 ===== */
    ::-webkit-scrollbar { width: 9px; height: 9px; }
    ::-webkit-scrollbar-thumb { background: #c5d3ea; border-radius: 9px; }
    ::-webkit-scrollbar-thumb:hover { background: #a9bfe3; }
    ::-webkit-scrollbar-track { background: transparent; }
    </style>""", unsafe_allow_html=True)


def render_top_nav():
    """顶部板块导航（参照参考应用：实验导览 / 决策台 / 复盘报告 等独立板块）"""
    s = st.session_state
    labels = [t for t, _ in PAGES]
    cur = PAGE_BY_ID[s.page]
    sel = st.pills("板块导航", labels, key="top_nav", default=cur,
                   label_visibility="collapsed", width="stretch")
    if sel:
        page_id = PAGE_BY_LABEL[sel]
        if page_id != s.page:
            s.page = page_id
            st.rerun()


def render_board(step_no):
    """独立板块页：26 复盘报告 / 27 能力画像 / 28 经营决策报告"""
    s = st.session_state
    st.markdown(
        f'<div style="background:linear-gradient(120deg,#0b3d91 0%,#1f6feb 100%);'
        f'border-radius:14px;padding:16px 22px;color:#fff;margin:6px 0 10px;'
        f'box-shadow:0 4px 14px rgba(11,61,145,0.2)">'
        f'<div style="font-size:22px;font-weight:700">{BOARD_NAMES[step_no]}</div>'
        f'<div style="font-size:13px;opacity:0.92;margin-top:4px">独立板块 · 基于「决策台」主线（第 1-25 步）过程数据自动生成</div></div>',
        unsafe_allow_html=True)
    if not main_done():
        st.info("主线尚未完成：请先在「🧭 决策台（25步）」完成第 1-25 步，本板块数据才能生成。")
        st.button("去决策台完成主线", type="primary", key=f"go_decision_{step_no}",
                  on_click=_nav_cb, args=("决策台",))
        return
    {26: render_step26, 27: render_step27, 28: render_step28}[step_no]()


def render_main():
    s = st.session_state
    if s.terminated:
        st.error("🚨 实验终止：因两次触碰同一红线，本次实验按失败处理。")
        st.info("系统判定依据：成本造假（材料单价>20）/ 虚增存货（在产品>完工×2）/ 责任甩锅（责任全推他人）。")
        if st.button("重新开始实验", type="primary", key="restart_main"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        return
    if s.page == "导览":
        render_landing()
        return
    if s.page != "决策台":
        render_board({"复盘": 26, "画像": 27, "报告": 28}[s.page])
        return
    # ===== 决策台（主线 1-25）=====
    if s.current_step >= 26:
        st.markdown(
            '<div style="background:linear-gradient(120deg,#2e9e5b 0%,#1f6feb 100%);'
            'border-radius:14px;padding:20px 24px;color:#fff;margin:6px 0 14px;'
            'box-shadow:0 4px 14px rgba(46,158,91,0.25)">'
            '<div style="font-size:24px;font-weight:700">🎉 决策台主线已完成</div>'
            '<div style="font-size:14px;opacity:0.94;margin-top:8px;line-height:1.7">'
            '第 1-25 步已全部完成。后续三个板块为独立输出，请通过**顶部板块导航**进入：'
            '📋 复盘报告（同口径复盘）· 🛡️ 能力画像（五维雷达）· '
            '📊 经营决策报告（定价/排产/考核建议与终结性评分）。</div></div>',
            unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("📋 复盘报告", type="primary", key="go_board_26", width="stretch",
                      on_click=_nav_cb, args=("复盘",))
        with c2:
            st.button("🛡️ 能力画像", type="primary", key="go_board_27", width="stretch",
                      on_click=_nav_cb, args=("画像",))
        with c3:
            st.button("📊 经营决策报告", type="primary", key="go_board_28", width="stretch",
                      on_click=_nav_cb, args=("报告",))
        return
    st.title("智控成本 · 数创价值")
    st.caption("制造企业全流程成本管理虚拟仿真决策实训 · 西南财经大学天府学院《成本管理会计 ACT1415A》课程组 · "
               f"{APP_VERSION} · 决策台（第 1-25 步）")
    completed = sum(1 for i in range(1, MAIN_FULL + 1) if i in s.decisions)
    st.progress(completed / MAIN_FULL)
    if s.milestone:
        st.success(s.milestone[1])
    # AI 建议（上一步）
    if s.current_step > 1 and s.current_step - 1 in s.ai_advice:
        with st.expander(f"🤖 AI 提分建议（第 {s.current_step - 1} 步后）", expanded=False):
            for t in s.ai_advice[s.current_step - 1]:
                st.markdown(f"- {t}")
    # 渲染当前步骤（主线 1-25）
    renderers = {1: render_step1, 2: render_step2, 3: render_step3, 4: render_step4,
                 5: render_step5, 6: render_step6, 7: render_step7, 8: render_step8,
                 9: render_step9, 10: render_step10, 11: render_step11, 12: render_step12,
                 13: render_step13, 14: render_step14, 15: render_step15, 16: render_step16,
                 17: render_step17, 18: render_step18, 19: render_step19, 20: render_step20,
                 21: render_step21, 22: render_step22, 23: render_step23, 24: render_step24,
                 25: render_step25}
    renderers.get(s.current_step, render_step1)()
    # 步骤旁计算器（仅需要计算的步骤显示）
    if s.current_step in CALC_HINTS:
        render_calculator(CALC_HINTS[s.current_step])
    if s.current_step > 1 and not s.terminated:
        st.divider()
        with st.expander("📖 学一点：小白化词条（按需查看）"):
            for term, info in GLOSSARY.items():
                st.markdown(f"**{term}**：{info['explain']}（案例：{info['case']}；样例：{info['sample']}）")


def main():
    st.set_page_config(page_title="智控成本·数创价值——成本管理虚拟仿真决策实训",
                       page_icon="🎯", layout="wide")
    inject_css()
    init_state()
    render_top_nav()
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
