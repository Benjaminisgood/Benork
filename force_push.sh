#!/bin/bash

# ========== 基本设置 ==========
DEFAULT_REMOTE="https://github.com/Benjaminisgood/Benork.git"
BRANCH_NAME="main"
COMMIT_MSG="💥 Force push to override remote repository"

# ========== GUI 弹窗函数 ==========
confirm_push() {
  osascript <<EOF
tell application "System Events"
    activate
    set response to display dialog "是否将本地代码覆盖远程仓库？\n\n仓库地址：$1" buttons {"取消", "继续"} default button "继续" with icon caution
    if button returned of response is "继续" then
        return "yes"
    else
        return "no"
    end if
end tell
EOF
}

# ========== 检查 .git ==========
if [ -d .git ]; then
  echo "✅ 当前目录已是 Git 仓库"
  CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)
  if [ -z "$CURRENT_REMOTE" ]; then
    echo "⚠️ 未设置远程仓库，将使用默认地址：$DEFAULT_REMOTE"
    git remote add origin "$DEFAULT_REMOTE"
    CURRENT_REMOTE=$DEFAULT_REMOTE
  else
    echo "🌐 当前远程仓库为：$CURRENT_REMOTE"
  fi
else
  echo "🚧 当前目录不是 Git 仓库，正在初始化..."
  git init
  git remote add origin "$DEFAULT_REMOTE"
  CURRENT_REMOTE=$DEFAULT_REMOTE
fi

# ========== 弹出确认对话框 ==========
response=$(confirm_push "$CURRENT_REMOTE")

if [ "$response" == "yes" ]; then
  echo "📦 开始强制覆盖推送..."

  git checkout -B "$BRANCH_NAME"        # 强制创建并切换分支
  git add .
  git commit -m "$COMMIT_MSG"

  git push -f origin "$BRANCH_NAME"
  echo "✅ 推送完成！"
else
  echo "❌ 用户取消操作。"
fi

# ========== 展示最终状态 ==========
echo ""
git remote -v
echo ""
git log --oneline -n 5