#!/bin/bash

# ⚠️ 请先确认以下信息是否正确
REMOTE_URL="https://github.com/Benjaminisgood/Benork.git"
BRANCH_NAME="main"
COMMIT_MSG="💥 Force push to override remote repository"

echo "🚀 开始执行 Git 强制覆盖推送流程..."

# 步骤 1：初始化 git 仓库
echo "📦 初始化 Git 仓库..."
git init

# 步骤 2：设置远程仓库
echo "🔗 设置远程地址为：$REMOTE_URL"
git remote add origin "$REMOTE_URL"

# 步骤 3：切换到主分支
echo "🌿 切换或创建分支：$BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# 步骤 4：添加全部文件
echo "📁 添加全部文件到 Git..."
git add .

# 步骤 5：提交更改
echo "✏️ 提交更改：$COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# 步骤 6：强制推送到远程仓库
echo "🚀 正在强制推送到远程仓库..."
git push -f origin "$BRANCH_NAME"

echo "✅ 完成！请到 GitHub 仓库查看是否成功同步。"

# 可选：显示远程地址和日志
echo "🌐 当前远程地址："
git remote -v

echo "🕘 最近提交历史："
git log --oneline -n 3