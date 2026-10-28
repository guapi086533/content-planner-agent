# GitHub 交付步骤

GitHub 交付仓库：[guapi086533/content-planner-agent](https://github.com/guapi086533/content-planner-agent)。默认分支为 `main`，所有代码、文档和验证材料位于同一仓库。

首次关联本地项目时，在项目根目录执行；若 `origin` 已存在则先核对地址，不重复添加。远程 URL 不包含密钥。

```powershell
git remote add origin https://github.com/guapi086533/content-planner-agent.git
git push -u origin main
git rev-parse HEAD
```

若 `origin` 已存在，先用 `git remote -v` 核对目标，确认后再调整。私有仓库需按照试卷要求添加指定评审账号；未提供的账号和题号不能自行编造。

建议提交信息：

```text
题号：填写试卷中“内容任务规划 Agent”的实际题号
GitHub URL：https://github.com/guapi086533/content-planner-agent
最终 commit SHA：粘贴 git rev-parse HEAD 的完整结果
运行入口：README.md
验证材料：examples/ 与 docs/03-evaluation.md
说明：50 项测试、14 组离线案例及 14 组真实模型场景状态/费用验收通过；业务工具为合成模拟
```

真实模型正常、预算降级及故障/部分成功路径已经补齐，见 examples/live/。模型公开说明仍需对照工具事实审查，单位问题的原始记录和修正复验分别保留。候选人还需补充真实个人修改与复验记录。补充材料会产生新提交，最后必须重新获取最终 SHA。

推送后检查[GitHub Actions](https://github.com/guapi086533/content-planner-agent/actions)中对应 SHA 的测试矩阵，并确认远程 `main` 与本地 HEAD 一致。GitHub 上传完成后，仍需按招聘方指定表单或邮件提交题号、仓库 URL 和完整 SHA；本项目没有代发招聘邮件或表单。
