# -*- coding: utf-8 -*-
"""AppTest 端到端：跑通 28 步全流程，断言四指标/红线/AI/报告"""
from streamlit.testing.v1 import AppTest

PASS, FAIL = [], []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"[PASS] {name}")
    else:
        FAIL.append(name)
        print(f"[FAIL] {name} {detail}")


def all_text(at):
    """聚合所有元素序列文本（markdown + success + info + caption + warning + error + metric + expander.label）"""
    parts = [str(e.value) for e in at.markdown]
    parts += [str(e.value) for e in at.success]
    parts += [str(e.value) for e in at.info]
    parts += [str(e.value) for e in at.caption]
    parts += [str(e.value) for e in at.warning]
    parts += [str(e.value) for e in at.error]
    parts += [str(m.value) for m in at.metric]
    parts += [str(m.value) for m in at.sidebar.metric]
    parts += [str(e.label) for e in at.expander]
    return " | ".join(parts)


def click(at, key):
    at.button(key=key).click()
    at.run()


def app_final_score(at):
    s = at.session_state
    perf = (s["indicators"] or {}).get("perf", 0)
    idea = s["decisions"].get(19, {}).get("ai_score", 0)
    qual = s["scores"].get("决策能力", 40)
    return min(100.0, 0.60 * perf + 0.20 * idea + 0.10 * qual
               + (10.0 if s["decisions"].get(18, {}).get("ok") else 0.0))


at = AppTest.from_file("main_app.py", default_timeout=120)
at.run()
landing_text = all_text(at) + " | " + " | ".join(str(t.value) for t in at.title)
check("着陆页标题渲染", "智控成本" in landing_text, landing_text[:150])
check("实验地图渲染", "实验地图" in landing_text, landing_text[:300])
check("逻辑主线渲染", "逻辑主线" in landing_text, landing_text[:300])
check("实训节奏渲染", "实训节奏" in landing_text, landing_text[:300])
check("实验介绍渲染", "实验介绍" in landing_text, landing_text[:300])
check("开始实验按钮存在", at.button(key="start_btn").value is not None,
      str(at.button(key="start_btn")))
click(at, "start_btn")
check("开始后进入第1步", at.session_state["current_step"] == 1,
      f"实际={at.session_state.get('current_step')}")
check("第1步内容渲染", "第 1 步" in all_text(at), all_text(at)[:150])
check("当前为第1步", at.session_state["current_step"] == 1)

# 步 1 → 9（默认推荐值）
for n in range(1, 10):
    click(at, f"fin_{n}")
    check(f"步{n}完成后进入第{n+1}步", at.session_state["current_step"] == n + 1,
          f"实际={at.session_state.get('current_step')}")

check("步9后四指标已计算", at.session_state["indicators"] is not None)
ind = at.session_state["indicators"]
check("默认单位成本≈421.43", abs(ind["unit_cost"] - 421.43) < 0.05, ind["unit_cost"])
check("默认利润为正", ind["profit"] > 0, ind["profit"])
check("责任绩效分>0且≤100", 0 < ind["perf"] <= 100, ind["perf"])
check("无红线触碰", sum(at.session_state["red_lines"].values()) == 0,
      at.session_state["red_lines"])

# 步 10 → 18（计算类步骤默认值均落在参考答案区间）
for n in range(10, 19):
    click(at, f"fin_{n}")
check("步18后进入第19步", at.session_state["current_step"] == 19,
      f"实际={at.session_state.get('current_step')}")

# 步 19 金点子（输入方案 + AI 判分）
at.text_area(key="s19_idea").set_value(
    "引入能耗数字化监控系统，按班组核算电费并纳入月度绩效，分阶段实施，"
    "预计每月节约 1.2 万元，成本费用下降 8%，财务部按月出具报表。")
at.run()
click(at, "s19_btn")
check("步19后进入第20步", at.session_state["current_step"] == 20,
      f"实际={at.session_state.get('current_step')}")
check("金点子AI评分>0", at.session_state["decisions"][19]["ai_score"] > 0,
      at.session_state["decisions"][19].get("ai_score"))

# 步 20 → 22（作业成本/动因博弈/责任中心）
for n in range(20, 23):
    click(at, f"fin_{n}")
check("步22后进入第23步", at.session_state["current_step"] == 23,
      f"实际={at.session_state.get('current_step')}")

# 步 23 数据仪表盘（独立按钮）
click(at, "s23_btn")
check("步23后进入第24步", at.session_state["current_step"] == 24,
      f"实际={at.session_state.get('current_step')}")

# 步 24 风险事件（二次确认）
click(at, "s24_btn")
check("步24后进入第25步", at.session_state["current_step"] == 25,
      f"实际={at.session_state.get('current_step')}")
check("风险事件已记录", "event_id" in at.session_state["decisions"].get(24, {}),
      at.session_state["decisions"].get(24, {}))

# 步 25 红线检查
click(at, "s25_btn")
check("步25后进入第26步", at.session_state["current_step"] == 26,
      f"实际={at.session_state.get('current_step')}")

# 步 26 复盘 / 步 27 画像 / 步 28 报告
click(at, "s26_btn")
check("步26后进入第27步", at.session_state["current_step"] == 27,
      f"实际={at.session_state.get('current_step')}")
click(at, "s27_btn")
check("步27后进入第28步", at.session_state["current_step"] == 28,
      f"实际={at.session_state.get('current_step')}")
txt28 = all_text(at)
check("步28报告含'经营决策报告'", "经营决策报告" in txt28 or "综合评分" in txt28, txt28[:200])
check("五维画像已计算", set(at.session_state["scores"].keys()) == {
    "核算准确", "成本分析", "决策能力", "业财融合", "创新意识"},
    at.session_state["scores"])
click(at, "s28_btn")
check("全部28步完成", len(at.session_state["decisions"]) >= 28,
      f"decisions={len(at.session_state['decisions'])}")

# 综合评分有限且在 0-100
score = app_final_score(at)
check("综合评分 0-100", 0 <= score <= 100, score)

print(f"\n=== AppTest 结果：PASS {len(PASS)} / {len(PASS) + len(FAIL)} ===")
if FAIL:
    print("FAILED:", FAIL)
    raise SystemExit(1)
print("ALL PASS")
