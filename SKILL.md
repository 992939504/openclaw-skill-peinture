---
name: peinture
description: Generate AI images via multiple providers (Hugging Face, Gitee AI). Free quota available on HF.
homepage: https://github.com/992939504/peinture
metadata:
  {
    "openclaw":
      {
        "emoji": "🎨",
        "requires": { "bins": ["python3"] }
      }
  }
---

# Peinture Image Generator

Generate AI images via multiple providers. Hugging Face offers free public quota.

## Providers

| Provider | Token Required | Models |
|----------|---------------|--------|
| `huggingface` (default) | Optional (free quota) | z-image-turbo, qwen-image-fast, ovis-image |
| `gitee` | Required (`GITEE_TOKEN`) | Qwen-Image, Z-Image-Turbo |

## Run

Note: Image generation can take longer than common exec timeouts (30s). Set a higher timeout when invoking via exec tool (e.g., exec timeout=120).

```bash
# Hugging Face (free, no token required)
python3 {baseDir}/scripts/gen.py --prompt "a beautiful sunset"

# Gitee AI (requires GITEE_TOKEN)
python3 {baseDir}/scripts/gen.py --provider gitee --model Qwen-Image --prompt "a cute cat"
```

## Options

```bash
# Provider selection
--provider huggingface  # Free Gradio Spaces (default)
--provider gitee        # Gitee AI

# Model selection (provider-specific)
--model z-image-turbo    # HF: Fast general model (default)
--model qwen-image-fast  # HF: Qwen image
--model ovis-image       # HF: Ovis 7B
--model Qwen-Image       # Gitee: Qwen
--model Z-Image-Turbo    # Gitee: Z-Image

# Aspect ratio
--ratio 1:1    # Square (default)
--ratio 16:9   # Landscape
--ratio 9:16   # Portrait
--ratio 4:3    # Standard
--ratio 3:4    # Portrait standard

# HD mode (higher resolution)
--hd

# Other options
--seed 12345   # Reproducible results
--steps 12     # Inference steps
--out-dir ./output  # Save to directory
--json         # JSON output
```

## Environment Variables

| Variable | Provider | Description |
|----------|----------|-------------|
| `HUGGING_FACE_TOKEN` or `HF_TOKEN` | huggingface | Optional, for higher rate limits |
| `GITEE_TOKEN` | gitee | Required |

## Getting Tokens

- **Hugging Face**: https://huggingface.co/settings/tokens (optional, free quota available)
- **Gitee AI**: https://ai.gitee.com/ → 控制台 → API 密钥 (required)

## Output

- Returns image URL (HF) or base64 data URL (Gitee)
- JSON output includes: prompt, provider, model, url, seed, dimensions

## Notes

- HF images hosted on Hugging Face may expire after 24 hours
- Gitee returns base64 images (embedded in response)
- Download images you want to keep