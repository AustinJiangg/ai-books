#!/usr/bin/env bash
# 图检查入口：node figcheck.mjs 的包装，自动带上 chromium 缺的系统库。
# 用法: tools/figcheck.sh [--png <目录>] <md 文件或目录>...
here="$(cd "$(dirname "$0")" && pwd)"
[ -d "$here/.chromium-libs" ] && export LD_LIBRARY_PATH="$here/.chromium-libs/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec node "$here/figcheck.mjs" "$@"
