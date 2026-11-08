# 素材审核与排期草稿 Agent

Python 3.10+，CLI，模型负责决策，代码校验红线。实现规格见 [spec/README.md](spec/README.md)。

安装（Windows PowerShell）：

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\schedule-agent.exe --help
.\.venv\Scripts\python.exe -m pytest
```

离线 Mock 仅验证流程，不证明真实模型决策效果。真实模型验证尚未执行。
任务进度见 [spec/07-tasks.md](spec/07-tasks.md)。
