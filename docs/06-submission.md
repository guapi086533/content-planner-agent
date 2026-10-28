# GitHub 交付步骤

当前交付范围由用户确认为“先完成本地项目和 Git 提交”。本轮没有创建或推送 GitHub 仓库。

在 GitHub 创建空仓库或确认已有目标仓库后，在项目根目录执行。下面的占位符需替换为真实地址；不要把私密 token 放入 URL。

```powershell
git remote add origin https://github.com/YOUR_ACCOUNT/content-planner-agent.git
git push -u origin main
git rev-parse HEAD
```

若 `origin` 已存在，先用 `git remote -v` 核对目标，确认后再调整。私有仓库需按照试卷要求添加指定评审账号；未提供的账号和题号不能自行编造。

建议提交信息：

```text
题号：填写试卷中“内容任务规划 Agent”的实际题号
GitHub URL：填写实际仓库 URL
最终 commit SHA：粘贴 git rev-parse HEAD 的完整结果
运行入口：README.md
验证材料：examples/ 与 docs/03-evaluation.md
说明：50 项测试、14 组离线案例及 14 组真实模型场景状态/费用验收通过；业务工具为合成模拟
```

真实模型正常、预算降级及故障/部分成功路径已经补齐，见 examples/live/。模型公开说明仍需对照工具事实审查，单位问题的原始记录和修正复验分别保留。候选人还需补充真实个人修改与复验记录。补充材料会产生新提交，最后必须重新获取最终 SHA。
