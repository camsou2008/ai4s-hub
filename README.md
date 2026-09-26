# AI4S 观测台

高校 AI for Science 基础设施动态观测站：每日信号扫描 → 早简报 → 深度调研。

- 线上站点：https://camsou2008.github.io/ai4s-hub/（GitHub Pages）
- 纯静态站（HTML + JS + JSON 数据），无构建步骤。
- 发布：把 `~/workspace/publish/ai4s` 下的 `index.html`、`api-data.js`、`assets/` 同步到本仓库对应位置，然后运行 `~/workspace/skills/github/bin/gh_push.py ~/workspace/repos/ai4s-hub camsou2008 ai4s-hub "<说明>"` 推送到 main 分支，GitHub Pages 约 1 分钟后自动上线。

## 定时任务（Asia/Shanghai）

- 信号扫描：每天 07:00
- 每日简报：每天 07:30
- 深度调研：按 48 小时规则
