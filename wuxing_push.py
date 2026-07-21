#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五行穿衣颜色推荐 - 每日推送引擎
基于当日日干天干推算五行穿搭建议，通过 Server酱 推送到微信。

用法:
  python wuxing_push.py            # 推送今日建议
  python wuxing_push.py --dry-run  # 打印消息但不推送
  python wuxing_push.py --date 2026-07-17  # 指定日期
"""

import io
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime

# 修复 Windows 控制台 emoji 输出
if os.name == 'nt':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ============================================================
#  配置
# ============================================================
SENDKEY = "SCT368025TN4uhG2lUXB8bqssxSNN6RwCq"
API_URL = f"https://sctapi.ftqq.com/{SENDKEY}.send"

# ============================================================
#  天干地支基础数据
# ============================================================
STEM_NAMES   = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
BRANCH_NAMES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
STEM_ELEM    = ['木','木','火','火','土','土','金','金','水','水']

WUXING = ['木','火','土','金','水']

# ============================================================
#  干支推算：以 1900-01-01 = 甲戌日（六十甲子序号10）为基准
# ============================================================
REF_DATE  = date(1900, 1, 1)
REF_CYCLE = 10

def ganzhi(d: date):
    """返回 (天干名, 地支名, 天干索引, 日干五行)"""
    days = (d - REF_DATE).days
    idx = (days + REF_CYCLE) % 60
    stem_idx = idx % 10
    branch_idx = idx % 12
    return STEM_NAMES[stem_idx], BRANCH_NAMES[branch_idx], stem_idx, STEM_ELEM[stem_idx]

# ============================================================
#  每日五行穿搭颜色规则
#  严格遵循五级分类：大吉(生我) > 次吉(同我) > 平色(我克) > 耗气(我生) > 大忌(克我)
# ============================================================

RULES = {
    # ---- 日干属木（甲、乙日）----
    '木': {
        '日干': '甲 / 乙',
        '大吉': {
            'color': '黑色、藏蓝色、深灰色',
            'swatch': '#1a2a3a',
            'relation': '水生木, 天时生扶',
            'desc': '贵人相助, 办事顺畅, 重要场合大面积穿戴',
        },
        '次吉': {
            'color': '绿色、青色、翠绿色',
            'swatch': '#4a7c59',
            'relation': '木同木, 比肩同频',
            'desc': '利于合作社交, 可搭配大吉色一同穿搭',
        },
        '平色': {
            'color': '黄色、咖色、驼色',
            'swatch': '#d4a017',
            'relation': '木克土, 我克为财',
            'desc': '宜求财洽谈, 仅袜子/腰带等小面积点缀',
        },
        '耗气': {
            'color': '红色、粉色、紫色',
            'swatch': '#c0392b',
            'relation': '木生火, 泄耗自身',
            'desc': '易疲惫内耗, 非必要不作主色, 仅极小额配饰',
        },
        '大忌': {
            'color': '白色、银灰色',
            'swatch': '#d0d0cc',
            'relation': '金克木, 天时冲克',
            'desc': '全天规避; 若仅此色系衣物, 内层小面积穿戴, 外层配大吉色',
        },
    },
    # ---- 日干属火（丙、丁日）----
    '火': {
        '日干': '丙 / 丁',
        '大吉': {
            'color': '绿色、青色、翠绿色',
            'swatch': '#4a7c59',
            'relation': '木生火, 天时生扶',
            'desc': '贵人相助, 办事顺畅, 重要场合大面积穿戴',
        },
        '次吉': {
            'color': '红色、粉色、紫色、橘红色',
            'swatch': '#c0392b',
            'relation': '火同火, 比肩同频',
            'desc': '利于合作社交, 可搭配大吉色一同穿搭',
        },
        '平色': {
            'color': '黄色、卡其色、驼色',
            'swatch': '#d4a017',
            'relation': '火克土, 我克为财',
            'desc': '宜求财洽谈, 仅袜子/腰带等小面积点缀',
        },
        '耗气': {
            'color': '白色、银灰色',
            'swatch': '#d0d0cc',
            'relation': '火生金, 泄耗自身',
            'desc': '易疲惫内耗, 非必要不作主色, 仅极小额配饰',
        },
        '大忌': {
            'color': '黑色、深蓝色',
            'swatch': '#1a2a3a',
            'relation': '水克火, 天时冲克',
            'desc': '全天规避; 若仅此色系衣物, 内层小面积穿戴, 外层配大吉色',
        },
    },
    # ---- 日干属土（戊、己日）----
    '土': {
        '日干': '戊 / 己',
        '大吉': {
            'color': '红色、粉色、紫色',
            'swatch': '#c0392b',
            'relation': '火生土, 天时生扶',
            'desc': '贵人相助, 办事顺畅, 重要场合大面积穿戴',
        },
        '次吉': {
            'color': '黄色、咖色、米色',
            'swatch': '#d4a017',
            'relation': '土同土, 比肩同频',
            'desc': '利于合作社交, 可搭配大吉色一同穿搭',
        },
        '平色': {
            'color': '白色、银色、浅灰色',
            'swatch': '#d0d0cc',
            'relation': '土克金, 我克为财',
            'desc': '宜求财洽谈, 仅袜子/腰带等小面积点缀',
        },
        '耗气': {
            'color': '黑色、藏蓝色',
            'swatch': '#1a2a3a',
            'relation': '土生水, 泄耗自身',
            'desc': '易疲惫内耗, 非必要不作主色, 仅极小额配饰',
        },
        '大忌': {
            'color': '绿色、青色',
            'swatch': '#4a7c59',
            'relation': '木克土, 天时冲克',
            'desc': '全天规避; 若仅此色系衣物, 内层小面积穿戴, 外层配大吉色',
        },
    },
    # ---- 日干属金（庚、辛日）----
    '金': {
        '日干': '庚 / 辛',
        '大吉': {
            'color': '黄色、咖色、驼色',
            'swatch': '#d4a017',
            'relation': '土生金, 天时生扶',
            'desc': '贵人相助, 办事顺畅, 重要场合大面积穿戴',
        },
        '次吉': {
            'color': '白色、银色、浅灰色',
            'swatch': '#d0d0cc',
            'relation': '金同金, 比肩同频',
            'desc': '利于合作社交, 可搭配大吉色一同穿搭',
        },
        '平色': {
            'color': '绿色、青色',
            'swatch': '#4a7c59',
            'relation': '金克木, 我克为财',
            'desc': '宜求财洽谈, 仅袜子/腰带等小面积点缀',
        },
        '耗气': {
            'color': '黑色、深蓝色',
            'swatch': '#1a2a3a',
            'relation': '金生水, 泄耗自身',
            'desc': '易疲惫内耗, 非必要不作主色, 仅极小额配饰',
        },
        '大忌': {
            'color': '红色、紫色、粉色',
            'swatch': '#c0392b',
            'relation': '火克金, 天时冲克',
            'desc': '全天规避; 若仅此色系衣物, 内层小面积穿戴, 外层配大吉色',
        },
    },
    # ---- 日干属水（壬、癸日）----
    '水': {
        '日干': '壬 / 癸',
        '大吉': {
            'color': '白色、银灰色、米白色',
            'swatch': '#d0d0cc',
            'relation': '金生水, 天时生扶',
            'desc': '贵人相助, 办事顺畅, 重要场合大面积穿戴',
        },
        '次吉': {
            'color': '黑色、藏蓝色、深灰色',
            'swatch': '#1a2a3a',
            'relation': '水同水, 比肩同频',
            'desc': '利于合作社交, 可搭配大吉色一同穿搭',
        },
        '平色': {
            'color': '红色、粉色、紫色',
            'swatch': '#c0392b',
            'relation': '水克火, 我克为财',
            'desc': '宜求财洽谈, 仅袜子/腰带等小面积点缀',
        },
        '耗气': {
            'color': '绿色、青色',
            'swatch': '#4a7c59',
            'relation': '水生木, 泄耗自身',
            'desc': '易疲惫内耗, 非必要不作主色, 仅极小额配饰',
        },
        '大忌': {
            'color': '黄色、咖色、土黄色',
            'swatch': '#d4a017',
            'relation': '土克水, 天时冲克',
            'desc': '全天规避; 若仅此色系衣物, 内层小面积穿戴, 外层配大吉色',
        },
    },
}

LEVEL_LABELS = {
    '大吉': '[大吉] 生扶色 (当日首选主色)',
    '次吉': '[次吉] 比肩色 (合作社交专用)',
    '平色': '[平色] 求财系 (仅小额点缀)',
    '耗气': '[耗气] 泄秀色 (尽量少穿)',
    '大忌': '[大忌] 相克色 (当日尽量不穿)',
}

LEVEL_ORDER = ['大吉', '次吉', '平色', '耗气', '大忌']

# ============================================================
#  场景化搭配建议
# ============================================================
SCENE_TIPS = [
    ('求职/签约/谈大单/求人办事',
     '全身以大吉色为主, 完全避开相克忌色'),
    ('商务合作/多人会议/社交聚会',
     '大吉色 + 次吉色双色搭配, 平衡人缘与机遇'),
    ('摆摊/销售/求财洽谈',
     '大吉色为主, 搭配少量平色求财配饰'),
    ('居家休息/独处放空',
     '可适度使用耗气色系, 舒缓情绪, 不影响运势'),
]

# ============================================================
#  消息构建
# ============================================================

def build_message(d: date):
    stem, branch, stem_idx, elem = ganzhi(d)

    weekday_names = ['周一','周二','周三','周四','周五','周六','周日']
    wd = weekday_names[d.weekday()]
    date_str = f"{d.year}年{d.month}月{d.day}日 {wd}"
    ganzhi_str = f"{stem}{branch}日"

    rule = RULES[elem]

    # 标题
    title = f"【五行穿衣】{date_str} | {stem}日({elem})"

    # 正文
    lines = []
    lines.append(f"**{date_str}**")
    lines.append(f"**{ganzhi_str}  日干属{elem}  ({rule['日干']})**")
    lines.append("")
    lines.append("---")
    lines.append("")

    for level in LEVEL_ORDER:
        r = rule[level]
        label = LEVEL_LABELS[level]
        lines.append(f"**{label}**")
        lines.append(f"> 推荐色系: {r['color']}")
        lines.append(f"> 原理: {r['relation']}")
        lines.append(f"> {r['desc']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("**场景差异化搭配参考**")
    lines.append("")

    for scene, tip in SCENE_TIPS:
        lines.append(f"- {scene}")
        lines.append(f"  {tip}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**主次面积配比**")
    lines.append("> 外层大衣/上衣/连衣裙: 70% 大吉色 + 30% 次吉色")
    lines.append("> 平色求财仅用于鞋袜/发饰/腰带, <= 10%")
    lines.append("> 耗气色仅应急点缀; 大忌色全天尽量不外露")
    lines.append("")
    lines.append("> 基于当日天干推算, 仅供参考")

    body = "\n".join(lines)
    return title, body


# ============================================================
#  Server酱 推送
# ============================================================

def send_push(title: str, body: str) -> bool:
    data = {
        'title': title,
        'desp': body,
    }
    payload = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(API_URL, data=payload, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            code = result.get('code', -1)
            if code == 0:
                pushid = result.get('data', {}).get('pushid', '')
                print(f"[OK] Push sent successfully: {pushid}")
                return True
            else:
                print(f"[FAIL] Push failed: {result.get('message', result)}")
                return False
    except Exception as e:
        print(f"[ERROR] Push exception: {e}")
        return False


# ============================================================
#  Main
# ============================================================

def main():
    target_date = date.today()

    # ---- 防重复：检查是否今天已推送 ----
    today_str = target_date.isoformat()
    try:
        with open('last_sent.txt', 'r') as f:
            if f.read().strip() == today_str:
                print(f'[SKIP] {today_str} already sent, skipping duplicate')
                return
    except FileNotFoundError:
        pass

    dry_run = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--dry-run':
            dry_run = True
        elif args[i] == '--date' and i + 1 < len(args):
            target_date = date.fromisoformat(args[i+1])
            i += 1
        elif args[i] == '--help' or args[i] == '-h':
            print(__doc__)
            return
        i += 1

    title, body = build_message(target_date)

    if dry_run:
        print("=" * 60)
        print(title)
        print("=" * 60)
        print(body)
        print("=" * 60)
        print("[DRY-RUN] Push not sent")
        return

    print(f"[INFO] Targeting: {target_date}")
    success = send_push(title, body)
    if success:
        # 立即写入标记文件，即使后续 git push 失败也不会重复发送
        with open('last_sent.txt', 'w') as f:
            f.write(today_str)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
