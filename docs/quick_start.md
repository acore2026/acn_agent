# ACN Agent Quick Start

## 1. 环境要求
- Python 3.10 及以上
- Linux / Ubuntu
- Windows 10 或 Windows 11 + PyCharm

## 2. 安装依赖
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. 配置参数
IDM、AgentGW、WebUI 的 IP 地址直接写在代码中，默认都是本机地址 `127.0.0.1`。如需修改，请直接编辑 [config.py](/home/acn/cxr/acn_agent/acn_agent/core/config.py) 中的 `Settings` 默认值。

默认配置如下：
```python
Settings(
    idm_host="127.0.0.1",
    agent_gw_host="127.0.0.1",
    webui_host="127.0.0.1",
)
```

## 4. 启动方式
Linux / Ubuntu 一键启动：
```bash
chmod +x scripts/start_acn_agent.sh
./scripts/start_acn_agent.sh
```

手动启动：
```bash
uvicorn acn_agent.main:app --host 0.0.0.0 --port 9010
```

PyCharm 启动建议：
- `Run/Debug Configurations` 中新增 `Python`
- `Module name` 填写 `uvicorn`
- `Parameters` 填写 `acn_agent.main:app --host 0.0.0.0 --port 9010`
- `Environment variables` 中设置 `PYTHONPATH` 为项目根目录

## 5. 运行测试
```bash
pytest
```

## 6. Mock 组件说明
仓库内置了以下 mock Python 程序，供本地联调使用：
- `mocks/idm_mock.py`
- `mocks/agent_gw_mock.py`
- `mocks/webui_mock.py`
- `mocks/acn_sdk_mock.py`

可按需用 `uvicorn` 或 `python -m` 直接运行。
