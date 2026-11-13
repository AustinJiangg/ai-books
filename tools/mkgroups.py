#!/usr/bin/env python3
"""从一本书的 README.md 生成 md-docs-site 的 groups.json（网页版左栏按「部分」分组）。

分组规则：
- README.md 单独放在最前（不显示组名）；README 里第一个「部分」标题之前引用的篇目也放在这一组。
- 「### 第X部分 …」或整行加粗的「**第X部分 …**」开始一个组，其下引用的 NN-xxx.md、A-xxx.md 归入该组。
- README 没引用到的 NN-xxx.md、A-xxx.md 放进「其他」组。
- STYLE.md、FIGURE-GUIDE.md、OUTLINE.md 放在最后的「写作说明」组。

用法（在仓库根目录）:
    python3 tools/mkgroups.py <书目录> <输出 groups.json>
    python3 .claude/skills/md-docs-site/scripts/build_docs_site.py \\
        --docs <书目录> --out html/<书目录>.html --groups <groups.json>
"""
import json
import os
import re
import sys

book, out = sys.argv[1:3]
files = sorted(os.listdir(book))
readme = open(os.path.join(book, 'README.md'), encoding='utf-8').read()
groups, seen = [["", ["README.md"]]], set()
cur = groups[0]
for line in readme.splitlines():
    m = re.match(r'^###\s+(.*)$', line) or re.match(r'^\*\*(第.+部分.*|附录.*)\*\*\s*$', line)
    if m:
        cur = [re.sub(r'\s+', ' ', m.group(1).replace('　', ' ')).strip(), []]
        groups.append(cur)
        continue
    for f in re.findall(r'\(((?:\d\d|[A-Z])-[^)#]+\.md)', line):
        if f in files and f not in seen:
            seen.add(f)
            cur[1].append(f)
groups = [g for g in groups if g[1]]
rest = [f for f in files if re.match(r"^(?:\d\d|[A-Z])-.*\.md$", f) and f not in seen]
if rest:
    groups.append(["其他", rest])
extra = [f for f in ('STYLE.md', 'FIGURE-GUIDE.md', 'OUTLINE.md') if f in files]
if extra:
    groups.append(["写作说明", extra])
with open(out, 'w', encoding='utf-8') as fp:
    json.dump(groups, fp, ensure_ascii=False)
print(book, [(g[0], len(g[1])) for g in groups])
