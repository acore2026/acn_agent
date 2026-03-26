# ACN Agent 接口文档

## 1. 基础信息
- 服务监听端口：`9010`
- 协议：HTTP
- 数据格式：`application/json`

## 2. 接口清单

| 接口路径 | 方法 | 上游目标 | 说明 |
| --- | --- | --- | --- |
| `/idm/v1/identity-applications` | POST | IDM:9020 | 身份申请消息转发 |
| `/arf/v1/agent-cards` | POST | AgentGW:9001 | Agent 卡片查询转发 |
| `/acn-agent/v1/task-executions` | POST | AgentGW:9001 | 任务执行请求转发 |
| `/acn-agent/v1/agent-deletions` | POST | IDM:9020 | Agent 删除请求转发 |
| `/acn-agent/v1/task-execution-terminations` | POST | AgentGW:9001 | 任务终止请求转发 |
| `/clear` | POST | 本地处理 | 清空 ACN Agent 本地缓存与打点 |
| `/health` | GET | 本地处理 | 健康检查及打点快照 |

## 3. clear 接口
请求示例：
```json
{}
```

响应示例：
```json
{
  "result": "success",
  "message": "本地状态清理完成",
  "cleared_records": 2,
  "cleared_pipeline_logs": 8
}
```

## 4. 流水日志说明
ACN Agent 在以下节点按需向 WebUI 推送 `/acn/v3/pipeline-logs`：
- 收到 ACN SDK 请求
- 请求转发至 IDM / AgentGW
- 收到上游响应
- 返回 ACN SDK 响应

日志体字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source` | string | 消息来源 |
| `destination` | string | 消息目的 |
| `timestamp` | string | UTC 时间戳 |
| `task_id` | string/null | 任务 ID，可选 |
| `protocol` | string | 协议名称 |
| `headers` | object/string | 请求头摘要 |
| `abstract` | string | 日志摘要 |
| `content` | object | 详细内容 |

## 5. 错误码
- `200/202`：上游调用成功，原样返回上游状态码
- `502`：调用 IDM / AgentGW / WebUI 时发生网络错误
