#!/usr/bin/env bash
# 用 md-docs-site skill 生成网页版 html/<书>.html：左栏按 README 的「部分」分组（tools/mkgroups.py），
# 指向别的书的 ../<书>/xx.md 链接改成跳到 <书>.html 的对应篇和小节。
# 用法（任意目录下）: tools/build-html.sh            # 重新生成 html/ 下已有的所有书
#                     tools/build-html.sh mmap mmio  # 只生成这几本
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

# 书 = html/ 下已有网页版、且仓库根下有同名目录的
all=()
for f in html/*.html; do b="$(basename "$f" .html)"; [ -f "$b/README.md" ] && all+=("$b"); done
[ $# -gt 0 ] && books=("$@") || books=("${all[@]}")

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
for b in "${books[@]}"; do
  [ -f "$b/README.md" ] || { echo "没有 $b/README.md" >&2; exit 1; }
  sib=()
  for o in "${all[@]}"; do [ "$o" != "$b" ] && sib+=(--sibling "$o=$o.html"); done
  python3 tools/mkgroups.py "$b" "$tmp/$b.json" >/dev/null
  echo "=== $b"
  python3 .claude/skills/md-docs-site/scripts/build_docs_site.py \
    --docs "$b" --out "html/$b.html" --groups "$tmp/$b.json" "${sib[@]}"
done
