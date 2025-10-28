# Secrets 管理（本地验证）

请在系统环境变量或`.env`中配置：

- `LLM_PROVIDER`：默认`qwen`（国内优先）。可选：`baidu|spark|hunyuan`。
- `LLM_API_KEY`：当使用OpenAI兼容调用或第三方代理时使用。
- `LLM_BASE_URL`：当走兼容端点时设置（示例：`https://api.openai.com/v1`或供应商兼容地址）。
- `ERNIE_API_KEY`、`SPARK_API_KEY`、`HUNYUAN_API_KEY`：对应官方SDK的密钥变量名（占位）。

建议使用系统安全存储或KMS/Vault进行加密与最小权限访问。
