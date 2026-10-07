# provider: d1jiema（D1 接码 / 易码）

## 定位

D1 是短信验证码接码平台。本 provider 已通过 `jiecode --provider d1jiema` 接入。

## 地址

- 官网：`https://www.d1jiema.com`
- API：`https://api.d1jiema.com/zc/data.php`
- 调用格式：`https://api.d1jiema.com/zc/data.php?code=<function>&token=<token>&...`

## 凭证与 OSS

凭证按 `ielym-certification api-key` provider 约定登记，取回命令：

```bash
ielym-certification api-key --name d1jiema --json
```

凭证对象路径为 `oss://<store-bucket>/certification/api-key/d1jiema/d1jiema.json`；Endpoint 由 `ielym-certification` 按运行环境返回（同地域走内网、跨地域走公网）。

## CLI 示例

```bash
jiecode --provider d1jiema status
jiecode --provider d1jiema get-phone --keyword 小红书
jiecode --provider d1jiema get-msg --phone 165xxxxxxxx --keyword 小红书
jiecode --provider d1jiema history
```

## API 字段

| 功能 | code | 参数 |
| --- | --- | --- |
| 查询余额 | `leftAmount` | token |
| 取号 | `getPhone` | token, keyWord 可选, phone 可选, province 可选, cardType 可选 |
| 取短信 | `getMsg` | token, phone 必填, keyWord 必填 |
| 历史记录 | `queryUsed` | token，每分钟最多一次 |

失败返回统一为 `ERROR:<信息>`。

## Token 创建

网页端 `apiToken.html` 当前显示“功能升级中”，但登录后后台命令仍可用：`trsCode=apiToken`，参数为 `acct\npassword\ndeviceType\ndeviceId\nverCode`。前提是账号已充值；未充值时返回 `只有已充值用户才能使用API`。

创建新 Token 后，同步更新本地配置和 OSS 凭证 JSON 的 `api_token` 字段。

## 使用约束

- 只用于低风险开发测试或合法业务场景。
- 实际取号会扣费，先执行 `jiecode --provider d1jiema status` 确认余额。
- 指定不存在的号码不会扣费，但如果确实取到号码就会进入计费流程。