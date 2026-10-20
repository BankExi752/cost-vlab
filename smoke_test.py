# -*- coding: utf-8 -*-
"""冒烟测试：算账引擎（标准例题逐位一致 + 7 边界用例）+ 红线 + AI 判定"""
import math
import main_app as app

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"[PASS] {name}")
    else:
        FAIL.append(name)
        print(f"[FAIL] {name} {detail}")


# ---------- 1. 标准例题手工验算（V4.0 3.4，教材口径） ----------
r = app.engine_calc(material_total=60000, processing_total=95000,
                    finished_qty=300, wip_qty=100,
                    material_pct=1.0, processing_pct=0.5)
check("材料约当产量=100", abs(r["mat_equiv"] - 100) < 1e-9, r)
check("加工约当产量=50", abs(r["proc_equiv"] - 50) < 1e-9, r)
check("材料单位成本=150.00", abs(r["mat_unit"] - 150.00) < 1e-6, r["mat_unit"])
check("加工单位成本=271.43", abs(r["proc_unit"] - 271.428571) < 1e-3, r["proc_unit"])
check("单位产品成本=421.43", abs(r["unit_cost"] - 421.428571) < 1e-3, r["unit_cost"])
check("完工产品成本=126428.57", abs(r["finished_cost"] - 126428.571) < 0.01, r["finished_cost"])
check("月末在产品成本=28571.43", abs(r["wip_cost"] - 28571.429) < 0.01, r["wip_cost"])
check("合计=155000.00（要素费用闭合）", abs(r["total_cost"] - 155000.0) < 0.01, r["total_cost"])

# ---------- 2. 四指标（默认配置：完全成本法/产销平衡/标准成本420） ----------
cfg = dict(app.DEFAULTS)
cfg["material_total"] = 60000.0
cfg["processing_total"] = 95000.0
cfg["labor_total"] = 50000.0
cfg["overhead"] = 45000.0
cfg["mat_unit_var"] = 150.0
cfg["labor_unit"] = 50000.0 / 350.0
cfg["std_unit"] = 420.0
cfg["sales_qty"] = 300
cfg["selling_price"] = 600.0
cfg["inv_adj"] = 1.0
cfg["cost_method"] = "完全成本法"
cfg["finished_add"] = 0
cfg["sales_mult"] = 1.0
cfg["price_mult"] = 1.0
cfg["overhead_add"] = 0.0
cfg["proc_mult"] = 1.0
ind = app.compute_indicators(cfg, {"成本造假": 0, "虚增存货": 0, "责任甩锅": 0})
check("默认单位成本≈421.43", abs(ind["unit_cost"] - 421.4286) < 0.01, ind["unit_cost"])
check("默认利润=53571.43（正）", abs(ind["profit"] - 53571.43) < 0.01, ind["profit"])
check("默认偏离=100.34% 绿", abs(ind["deviation"] - 100.3401) < 0.05 and ind["deviation_color"] == "绿",
      (ind["deviation"], ind["deviation_color"]))
check("默认绩效分≈94.32", abs(ind["perf"] - 94.3198) < 0.05, ind["perf"])

# ---------- 3. 偏离指数颜色区间 ----------
check("偏离95=蓝", app.deviation_color(95) == "蓝")
check("偏离95.01=绿", app.deviation_color(95.01) == "绿")
check("偏离105=绿", app.deviation_color(105) == "绿")
check("偏离105.01=黄", app.deviation_color(105.01) == "黄")
check("偏离115=黄", app.deviation_color(115) == "黄")
check("偏离115.01=红", app.deviation_color(115.01) == "红")

# ---------- 4. 绩效分公式（低于95%也扣分，防偷工减料） ----------
check("绩效分@偏离100=95", abs(app.perf_score(100) - 95.0) < 1e-9)
check("绩效分@偏离104=87", abs(app.perf_score(104) - 87.0) < 1e-9)
check("绩效分@偏离90=75", abs(app.perf_score(90) - 75.0) < 1e-9)
check("绩效分@偏离50 截断0", app.perf_score(50) == 0.0)

# ---------- 5. 红线判定 ----------
dec3_high = {3: {"unit_price": 22.0}, 22: {"center_choice": "正常"}}
cfg_rl = dict(cfg); cfg_rl["wip_qty"] = 100; cfg_rl["finished_qty"] = 300
check("红线：单价>20 → 成本造假",
      "成本造假" in app.red_line_status(cfg_rl, dec3_high))
cfg_rl2 = dict(cfg); cfg_rl2["wip_qty"] = 700; cfg_rl2["finished_qty"] = 300
check("红线：在产品>完工×2 → 虚增存货",
      "虚增存货" in app.red_line_status(cfg_rl2, {3: {"unit_price": 12.0}}))
cfg_rl3 = dict(cfg); cfg_rl3["wip_qty"] = 100
check("红线：责任全推他人 → 责任甩锅",
      "责任甩锅" in app.red_line_status(cfg_rl3, {22: {"center_choice": "全部推给他方"}}))
check("红线：正常配置不触发", app.red_line_status(cfg_rl, {3: {"unit_price": 12.0}}) == [])

# ---------- 6. 红线扣分 ----------
ind_pen = app.compute_indicators(cfg, {"成本造假": 1, "虚增存货": 0, "责任甩锅": 0})
check("红线扣30分", abs(ind_pen["perf"] - (94.3198 - 30.0)) < 0.05, ind_pen["perf"])

# ---------- 7. 7 个边界用例（TC-A-01~07）：无崩溃/无溢出/无逻辑异常 ----------
tc_cases = [
    ("TC-A-01 正常（300/100/1.0/0.5）", 300, 100, 1.0, 0.5),
    ("TC-A-02 零在产品", 300, 0, 1.0, 0.5),
    ("TC-A-03 全部在产品", 0, 100, 1.0, 0.5),
    ("TC-A-04 完工100%", 300, 100, 1.0, 1.0),
    ("TC-A-05 完工0%（加工完工程度0）", 300, 100, 1.0, 0.0),
    ("TC-A-06 极小采购（价5量1000）", 300, 100, 1.0, 0.5),
    ("TC-A-07 极大采购（价20量10000）", 300, 100, 1.0, 0.5),
]
for name, fq, wq, mp, pp in tc_cases:
    mat_total = 60000.0 if "采购" not in name else (5000.0 if "极小" in name else 200000.0)
    r = app.engine_calc(mat_total, 95000.0, fq, wq, mp, pp)
    finite = all(math.isfinite(v) for v in (r["mat_unit"], r["proc_unit"], r["unit_cost"],
                                            r["finished_cost"], r["wip_cost"], r["total_cost"]))
    positive = r["mat_unit"] >= 0 and r["proc_unit"] >= 0
    closed = abs(r["total_cost"] - (r["finished_cost"] + r["wip_cost"])) < 1e-6
    check(f"{name} 无崩溃/有限/闭合", finite and positive and closed, r)

# ---------- 8. AI 金点子判定（规则引擎） ----------
s1, c1, d1 = app.ai_score_idea("引入能耗数字化监控系统，按班组核算电费并纳入月度绩效，"
                                "分阶段实施，预计每月节约 1.2 万元，成本费用下降 8%，财务部按月出具报表。")
check("金点子优秀方案 ≥85", s1 >= 85 and 0 <= s1 <= 100, s1)
check("金点子四维权重合计=100", abs(sum(app.AI_DIMS[k][1] for k in app.AI_DIMS) - 100.0) < 1e-9)
s2, c2, _ = app.ai_score_idea("好")
check("金点子过短 ≤40", s2 <= 40, s2)
s3, c3, _ = app.ai_score_idea("")
check("金点子空文本 ≤40", s3 <= 40, s3)

# ---------- 9. AI 提分建议 ----------
adv = app.ai_step_advice(6, None, {"deviation": 120.0, "profit": -1000.0, "perf": 50.0},
                         dict(cfg), {6: {"ok": False}})
check("AI建议3条且含偏离/亏损/绩效", len(adv) == 3 and any("120" in a for a in adv), adv)

# ---------- 汇总 ----------
print(f"\n=== 冒烟结果：PASS {len(PASS)} / {len(PASS) + len(FAIL)} ===")
if FAIL:
    print("FAILED:", FAIL)
    raise SystemExit(1)
print("ALL PASS")
