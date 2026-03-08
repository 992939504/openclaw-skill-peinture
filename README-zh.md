# Peinture

🎨 **OpenClaw（大龙虾）** AI 图像生成技能。支持多平台自动切换。

## 功能特点

- 多平台支持：Hugging Face（免费）和 Gitee AI
- 自动故障转移
- 多模型支持：Z-Image-Turbo、Qwen-Image、Ovis-Image
- 支持多种宽高比和高清模式
- JSON 输出便于程序调用

## 安装

将 `peinture` 文件夹复制到 OpenClaw 技能目录：

```bash
cp -r peinture ~/.openclaw/skills/
```

Docker 部署时，挂载到配置目录即可。

## 使用方法

### 命令行

```bash
# 基本用法（Hugging Face，免费）
python3 scripts/gen.py --prompt "美丽的日落风景"

# 指定模型
python3 scripts/gen.py --prompt "赛博朋克城市" --model qwen-image-fast

# Gitee AI（需要 Token）
export GITEE_TOKEN=你的token
python3 scripts/gen.py --provider gitee --model Qwen-Image --prompt "可爱的猫咪"
```

### OpenClaw 集成

技能会被 OpenClaw 自动识别，直接让 AI 生成图片即可：

```
生成一张海上日落的图片
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--prompt` | （必填） | 图片生成提示词 |
| `--provider` | huggingface | 平台：`huggingface` 或 `gitee` |
| `--model` | z-image-turbo | 模型名称（见下表） |
| `--ratio` | 1:1 | 宽高比：1:1、16:9、9:16、4:3、3:4、3:2、2:3 |
| `--hd` | false | 启用高清模式（2倍分辨率） |
| `--seed` | 随机 | 随机种子，用于复现结果 |
| `--steps` | 模型默认 | 推理步数 |
| `--out-dir` | （无） | 保存图片到指定目录 |
| `--json` | false | 以 JSON 格式输出结果 |

## 模型列表

### Hugging Face（免费）

| 模型 | 说明 |
|------|------|
| `z-image-turbo` | 快速通用模型（默认） |
| `qwen-image-fast` | 通义万相图像生成 |
| `ovis-image` | Ovis 7B 图像生成 |

### Gitee AI（需要 Token）

| 模型 | 说明 |
|------|------|
| `Qwen-Image` | 通义万相图像生成 |
| `Z-Image-Turbo` | Z-Image Turbo |

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `HUGGING_FACE_TOKEN` 或 `HF_TOKEN` | 可选，用于提高 HF 调用频率 |
| `GITEE_TOKEN` | 必填，Gitee AI 所需 |

## 获取 API Token

### Hugging Face（可选）

1. 访问 https://huggingface.co/settings/tokens
2. 创建 Access Token（Read 权限即可）
3. 设置环境变量：`HUGGING_FACE_TOKEN=hf_xxx`

> Hugging Face 免费用户有公开配额，不设置 Token 也能使用，但频率较低。

### Gitee AI

1. 访问 https://ai.gitee.com/
2. 登录后进入控制台 → API 密钥
3. 创建密钥并复制
4. 设置环境变量：`GITEE_TOKEN=xxx`

## 安全提示

- 不要将 Token 硬编码到代码中
- 不要将 Token 提交到 Git 仓库
- 使用环境变量存储 Token
- Docker 部署时通过 `environment` 注入：

```yaml
# docker-compose.yml 示例
environment:
  - HUGGING_FACE_TOKEN=${HUGGING_FACE_TOKEN}
  - GITEE_TOKEN=${GITEE_TOKEN}
```

或使用 `.env` 文件（不要提交到仓库）：

```bash
# .env 文件
HUGGING_FACE_TOKEN=hf_你的token
GITEE_TOKEN=你的gitee_token
```

## 致谢

本项目基于 [Amery2010/peinture](https://github.com/Amery2010/peinture) 开发，感谢原作者的基础实现。

## 许可证

MIT
