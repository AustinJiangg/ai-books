#!/usr/bin/env bash
# 把 AgentENV 手册的代码基线拉到仓库根下的 .src/（不入库）。已存在的目录不重复拉取。
# 用法: tools/fetch-sources.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
src="$root/.src"; mkdir -p "$src"; cd "$src"

if [ ! -d agentenv ]; then
  git clone -q https://github.com/kvcache-ai/AgentENV agentenv
fi
git -C agentenv checkout -q v0.2.3

if [ ! -d fc-aenv ]; then
  git clone -q --filter=blob:none https://github.com/kvcache-ai/firecracker fc-aenv
  git -C fc-aenv remote add upstream https://github.com/firecracker-microvm/firecracker
  git -C fc-aenv fetch -q upstream tag v1.15.1 --no-tags
fi
git -C fc-aenv checkout -q aenv-deps

if [ ! -d e2b-infra ]; then
  git clone -q --filter=blob:none https://github.com/e2b-dev/infra e2b-infra
fi
git -C e2b-infra checkout -q 2026.09

if [ ! -d overlaybd-upstream ]; then
  git clone -q --depth 1 https://github.com/containerd/overlaybd overlaybd-upstream
fi

echo "agentenv   $(git -C agentenv rev-parse --short=12 HEAD)  (v0.2.3)"
echo "fc-aenv    $(git -C fc-aenv rev-parse --short=12 HEAD)  (aenv-deps)"
echo "e2b-infra  $(git -C e2b-infra rev-parse --short=12 HEAD)  (2026.09)"
echo "overlaybd  $(git -C overlaybd-upstream rev-parse --short=12 HEAD)  (containerd/overlaybd main)"
