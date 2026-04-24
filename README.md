# Juben Workspace

这个仓库当前维护的是一个 reviewer-only 的小说改编短剧流水线。

主项目在：
- [G:\Juben\juben](/G:/Juben/juben)

建议从这里开始看：
- [G:\Juben\juben\README.md](/G:/Juben/juben/README.md)
- [G:\Juben\juben\harness\framework\entry.md](/G:/Juben/juben/harness/framework/entry.md)
- [G:\Juben\juben\_ops\controller.py](/G:/Juben/juben/_ops/controller.py)

当前主流程：
1. `init`
2. `extract-book`
3. `map-book`
4. `start batchXX`
5. `start batchXX --write`
6. `batch-review-done`
7. `run batchXX`
8. `record`
