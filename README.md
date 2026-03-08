# Peinture

🎨 AI image generation skill for **OpenClaw** (大龙虾). Generate images via multiple providers with automatic fallback.

## Features

- Multiple providers: Hugging Face (free) and Gitee AI
- Automatic fallback between providers
- Multiple models: Z-Image-Turbo, Qwen-Image, Ovis-Image
- Aspect ratio and HD mode support
- JSON output for programmatic use

## Installation

Copy the `peinture` folder to your OpenClaw skills directory:

```bash
cp -r peinture ~/.openclaw/skills/
```

Or for Docker deployments, mount it in your config directory.

## Usage

### Command Line

```bash
# Basic usage (Hugging Face, free)
python3 scripts/gen.py --prompt "a beautiful sunset over mountains"

# Specify model
python3 scripts/gen.py --prompt "cyberpunk city" --model qwen-image-fast

# Gitee AI (requires token)
export GITEE_TOKEN=your_token_here
python3 scripts/gen.py --provider gitee --model Qwen-Image --prompt "cute cat"
```

### OpenClaw Integration

The skill is automatically recognized by OpenClaw. Just ask the AI to generate an image:

```
Generate an image of a sunset over the ocean
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--prompt` | (required) | Text prompt for image generation |
| `--provider` | huggingface | Provider: `huggingface` or `gitee` |
| `--model` | z-image-turbo | Model name (see below) |
| `--ratio` | 1:1 | Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3 |
| `--hd` | false | Enable 2x resolution |
| `--seed` | random | Random seed for reproducibility |
| `--steps` | model default | Inference steps |
| `--out-dir` | (none) | Save image to directory |
| `--json` | false | Output result as JSON |

## Models

### Hugging Face (Free)

| Model | Description |
|-------|-------------|
| `z-image-turbo` | Fast general-purpose model (default) |
| `qwen-image-fast` | Qwen image generation |
| `ovis-image` | Ovis 7B image generation |

### Gitee AI (Requires Token)

| Model | Description |
|-------|-------------|
| `Qwen-Image` | Qwen image generation |
| `Z-Image-Turbo` | Z-Image Turbo |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HUGGING_FACE_TOKEN` or `HF_TOKEN` | Optional, for higher rate limits on HF |
| `GITEE_TOKEN` | Required for Gitee AI |

## Getting API Tokens

### Hugging Face (Optional)

1. 访问 https://huggingface.co/settings/tokens
2. 创建 Access Token（Read 权限即可）
3. 设置环境变量：`HUGGING_FACE_TOKEN=hf_xxx`

> Hugging Face 免费用户有公开配额，不设 Token 也能使用，但频率较低。

### Gitee AI

1. 访问 https://ai.gitee.com/
2. 登录后进入控制台 → API 密钥
3. 创建密钥并复制
4. 设置环境变量：`GITEE_TOKEN=xxx`

## License

MIT
