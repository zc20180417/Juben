# Juben Workspace

这是一个 agent-native 的小说改编竖屏短剧生产工具包。Python 负责初始化、生成 prompt packet、维护状态和导出结果；大模型 agent 负责抽取、分集、写剧本和评审。

主项目在：
- [G:\Juben\juben](/G:/Juben/juben)

V1 使用入口：

```powershell
.\~init.cmd "被弃真千金：总裁不好惹.md" --episodes 25 --target-total-minutes 50
.\~extract.cmd
.\~map.cmd
.\~start.cmd batch01 --write
.\~review.cmd batch01 PASS --reviewer codex
.\~run.cmd batch01
.\~record.cmd batch01
.\~next.cmd
```

常用辅助命令：

```powershell
.\~status.cmd
.\~export.cmd
.\~check.cmd batch01
.\~clean.cmd
```

输出入口：
- [G:\Juben\juben\output\SUMMARY.md](/G:/Juben/juben/output/SUMMARY.md)
- [G:\Juben\juben\output\manifest.json](/G:/Juben/juben/output/manifest.json)
- [G:\Juben\juben\output\episodes](/G:/Juben/juben/output/episodes)
- [G:\Juben\juben\output\_runtime](/G:/Juben/juben/output/_runtime)：内部诊断材料，普通交付可忽略

部署文档：
- [G:\Juben\docs\deployment\local-agent-pack-v1.md](/G:/Juben/docs/deployment/local-agent-pack-v1.md)
- [G:\Juben\docs\deployment\operator-guide.md](/G:/Juben/docs/deployment/operator-guide.md)
- [G:\Juben\docs\deployment\output-package-v1.md](/G:/Juben/docs/deployment/output-package-v1.md)
- [G:\Juben\docs\deployment\troubleshooting.md](/G:/Juben/docs/deployment/troubleshooting.md)
