#!/usr/bin/env python3
"""
Peinture Image Generator - Generate AI images via multiple providers.
Supports Hugging Face (free) and Gitee AI.
"""

import argparse
import base64
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# ============================================================================
# PROVIDER CONFIGURATIONS
# ============================================================================

# Hugging Face Gradio Spaces (free public quota)
HF_MODEL_ENDPOINTS = {
    "z-image-turbo": {
        "base_url": "https://luca115-z-image-turbo.hf.space",
        "endpoint": "/gradio_api/call/generate_image",
    },
    "qwen-image-fast": {
        "base_url": "https://mcp-tools-qwen-image-fast.hf.space",
        "endpoint": "/gradio_api/call/generate_image",
    },
    "ovis-image": {
        "base_url": "https://aidc-ai-ovis-image-7b.hf.space",
        "endpoint": "/gradio_api/call/generate",
    },
}

# Gitee AI (requires token)
GITEE_API_URL = "https://ai.gitee.com/v1/images/generations"
GITEE_MODELS = {
    "Qwen-Image": "Qwen-Image",
    "Z-Image-Turbo": "Tongyi-MAI/Z-Image-Turbo",
}

# Default dimensions for aspect ratios (non-HD)
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1024, 576),
    "9:16": (576, 1024),
    "4:3": (1024, 768),
    "3:4": (768, 1024),
    "3:2": (960, 640),
    "2:3": (640, 960),
}

# HD dimensions (2x resolution)
ASPECT_RATIOS_HD = {
    "1:1": (2048, 2048),
    "16:9": (2048, 1152),
    "9:16": (1152, 2048),
    "4:3": (2048, 1536),
    "3:4": (1536, 2048),
    "3:2": (1920, 1280),
    "2:3": (1280, 1920),
}

# Default steps per model
DEFAULT_STEPS = {
    "z-image-turbo": 9,
    "qwen-image-fast": 8,
    "ovis-image": 24,
    "Qwen-Image": 9,
    "Z-Image-Turbo": 9,
}

RETRYABLE_HTTP_CODES = {401, 403, 429}
RETRYABLE_ERROR_PATTERNS = [
    "rate limit",
    "quota",
    "too many requests",
    "unauthorized",
    "forbidden",
    "queue",
    "capacity",
    "overloaded",
    "temporarily unavailable",
    "timeout",
    "timed out",
    "api returned error event",
    "connection reset",
    "bad gateway",
    "service unavailable",
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_auth_headers(token: str | None) -> dict[str, str]:
    """Return authorization headers if token is provided."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def is_retryable_error(exc: Exception) -> bool:
    """Return True when a request should be retried."""
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in RETRYABLE_HTTP_CODES:
            return True
        try:
            body = exc.read().decode("utf-8", errors="replace").lower()
        except Exception:
            body = ""
        return any(pattern in body for pattern in RETRYABLE_ERROR_PATTERNS)

    message = str(exc).lower()
    return any(pattern in message for pattern in RETRYABLE_ERROR_PATTERNS)


def log(provider: str, message: str) -> None:
    print(f"[{provider}] {message}", file=sys.stderr)


def extract_complete_event_data(sse_stream: str) -> dict | None:
    """Extract data from SSE 'complete' event (for HF Gradio)."""
    lines = sse_stream.split("\n")
    is_complete_event = False

    for line in lines:
        if line.startswith("event:"):
            event_type = line[6:].strip()
            if event_type == "complete":
                is_complete_event = True
            elif event_type == "error":
                raise RuntimeError("API returned error event")
            else:
                is_complete_event = False
        elif line.startswith("data:") and is_complete_event:
            json_data = line[5:].strip()
            try:
                return json.loads(json_data)
            except json.JSONDecodeError:
                continue
    return None


def download_image(url: str, out_path: Path) -> None:
    """Download image from URL to file."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        out_path.write_bytes(resp.read())


def save_base64_image(b64_data: str, out_path: Path) -> None:
    """Save base64 image data to file."""
    if b64_data.startswith("data:"):
        b64_data = b64_data.split(",", 1)[1]
    image_data = base64.b64decode(b64_data)
    out_path.write_bytes(image_data)


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:50] or "image"


# ============================================================================
# HUGGING FACE (GRADIO SPACES)
# ============================================================================


def generate_hf_z_image(prompt: str, width: int, height: int, seed: int, steps: int, token: str | None) -> str:
    """Generate image using Z-Image Turbo on HF."""
    base_url = HF_MODEL_ENDPOINTS["z-image-turbo"]["base_url"]
    queue_url = f"{base_url}/gradio_api/call/generate_image"
    payload = {"data": [prompt, height, width, steps, seed, False]}

    req = urllib.request.Request(
        queue_url,
        method="POST",
        headers=get_auth_headers(token),
        data=json.dumps(payload).encode("utf-8"),
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Queue request failed ({e.code}): {body}") from e

    event_id = result.get("event_id")
    if not event_id:
        raise RuntimeError(f"No event_id in response: {result}")

    result_url = f"{base_url}/gradio_api/call/generate_image/{event_id}"
    req = urllib.request.Request(result_url, headers=get_auth_headers(token))

    max_wait = 120
    start = time.time()
    while time.time() - start < max_wait:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                sse_data = resp.read().decode("utf-8")
                data = extract_complete_event_data(sse_data)
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0].get("url", "")
        except urllib.error.HTTPError:
            pass
        time.sleep(2)

    raise RuntimeError("Timeout waiting for image generation")


def generate_hf_qwen_image(prompt: str, aspect_ratio: str, seed: int | None, steps: int, token: str | None) -> tuple[str, int]:
    """Generate image using Qwen Image Fast on HF."""
    base_url = HF_MODEL_ENDPOINTS["qwen-image-fast"]["base_url"]
    use_random_seed = seed is None
    actual_seed = seed if seed is not None else 42

    queue_url = f"{base_url}/gradio_api/call/generate_image"
    payload = {"data": [prompt, actual_seed, use_random_seed, aspect_ratio, 3, steps]}

    req = urllib.request.Request(
        queue_url,
        method="POST",
        headers=get_auth_headers(token),
        data=json.dumps(payload).encode("utf-8"),
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Queue request failed ({e.code}): {body}") from e

    event_id = result.get("event_id")
    if not event_id:
        raise RuntimeError(f"No event_id in response: {result}")

    result_url = f"{base_url}/gradio_api/call/generate_image/{event_id}"
    req = urllib.request.Request(result_url, headers=get_auth_headers(token))

    max_wait = 120
    start = time.time()
    while time.time() - start < max_wait:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                sse_data = resp.read().decode("utf-8")
                data = extract_complete_event_data(sse_data)
                if data and isinstance(data, list) and len(data) >= 2:
                    url = data[0].get("url", "")
                    seed_str = data[1] if isinstance(data[1], str) else ""
                    match = re.search(r"\d+", seed_str)
                    actual_seed = int(match.group()) if match else actual_seed
                    return url, actual_seed
        except urllib.error.HTTPError:
            pass
        time.sleep(2)

    raise RuntimeError("Timeout waiting for image generation")


def generate_hf_ovis_image(prompt: str, width: int, height: int, seed: int, steps: int, token: str | None) -> str:
    """Generate image using Ovis Image on HF."""
    base_url = HF_MODEL_ENDPOINTS["ovis-image"]["base_url"]
    queue_url = f"{base_url}/gradio_api/call/generate"
    payload = {"data": [prompt, height, width, seed, steps, 4]}

    req = urllib.request.Request(
        queue_url,
        method="POST",
        headers=get_auth_headers(token),
        data=json.dumps(payload).encode("utf-8"),
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Queue request failed ({e.code}): {body}") from e

    event_id = result.get("event_id")
    if not event_id:
        raise RuntimeError(f"No event_id in response: {result}")

    result_url = f"{base_url}/gradio_api/call/generate/{event_id}"
    req = urllib.request.Request(result_url, headers=get_auth_headers(token))

    max_wait = 180
    start = time.time()
    while time.time() - start < max_wait:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                sse_data = resp.read().decode("utf-8")
                data = extract_complete_event_data(sse_data)
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0].get("url", "")
        except urllib.error.HTTPError:
            pass
        time.sleep(2)

    raise RuntimeError("Timeout waiting for image generation")


def generate_hf(model: str, prompt: str, width: int, height: int, aspect_ratio: str, seed: int, input_seed: int | None, steps: int, token: str | None) -> str | tuple[str, int]:
    """Generate image using Hugging Face Gradio Spaces."""
    if model == "z-image-turbo":
        return generate_hf_z_image(prompt, width, height, seed, steps, token)
    if model == "qwen-image-fast":
        return generate_hf_qwen_image(prompt, aspect_ratio, input_seed, steps, token)
    if model == "ovis-image":
        return generate_hf_ovis_image(prompt, width, height, seed, steps, token)
    raise RuntimeError(f"Unsupported HF model: {model}")


# ============================================================================
# GITEE AI
# ============================================================================


def generate_gitee(model: str, prompt: str, width: int, height: int, seed: int, steps: int, token: str) -> str:
    """Generate image using Gitee AI. Returns base64 data URL."""
    model_id = GITEE_MODELS.get(model)
    if not model_id:
        raise RuntimeError(f"Unsupported Gitee model: {model}")

    payload = {
        "prompt": prompt,
        "model": model_id,
        "width": width,
        "height": height,
        "seed": seed,
        "num_inference_steps": steps,
    }

    req = urllib.request.Request(
        GITEE_API_URL,
        method="POST",
        headers=get_auth_headers(token),
        data=json.dumps(payload).encode("utf-8"),
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gitee AI error ({e.code}): {body}") from e

    if not result.get("data") or not result["data"][0].get("b64_json"):
        raise RuntimeError(f"Invalid Gitee AI response: {result}")

    b64_image = result["data"][0]["b64_json"]
    mime_type = result["data"][0].get("type", "image/png")
    return f"data:{mime_type};base64,{b64_image}"


# ============================================================================
# RETRY PLAN
# ============================================================================


def build_attempt_plan(requested_provider: str, requested_model: str, hf_token: str | None, gitee_token: str | None) -> list[dict]:
    """Build ordered retry attempts across providers."""
    attempts: list[dict] = []

    def add_attempt(provider: str, model: str, auth_mode: str, token: str | None) -> None:
        attempt = {
            "provider": provider,
            "model": model,
            "auth_mode": auth_mode,
            "token": token,
        }
        if attempt not in attempts:
            attempts.append(attempt)

    def add_hf_chain(model: str) -> None:
        add_attempt("huggingface", model, "public", None)
        if hf_token:
            add_attempt("huggingface", model, "private", hf_token)

    def add_qwen_fallbacks() -> None:
        if gitee_token:
            add_attempt("gitee", "Qwen-Image", "token", gitee_token)

    def add_zimage_fallbacks() -> None:
        if gitee_token:
            add_attempt("gitee", "Z-Image-Turbo", "token", gitee_token)

    if requested_provider == "huggingface":
        add_hf_chain(requested_model)
        if requested_model == "qwen-image-fast":
            add_qwen_fallbacks()
        elif requested_model in {"z-image-turbo", "ovis-image"}:
            add_zimage_fallbacks()
    elif requested_provider == "gitee":
        if requested_model == "Qwen-Image":
            add_hf_chain("qwen-image-fast")
            add_attempt("gitee", requested_model, "token", gitee_token)
        elif requested_model == "Z-Image-Turbo":
            add_hf_chain("z-image-turbo")
            add_attempt("gitee", requested_model, "token", gitee_token)
        else:
            add_attempt("gitee", requested_model, "token", gitee_token)

    return attempts


def run_attempt(attempt: dict, prompt: str, width: int, height: int, aspect_ratio: str, seed: int, input_seed: int | None, steps: int):
    """Execute one attempt."""
    provider = attempt["provider"]
    model = attempt["model"]
    token = attempt["token"]

    if provider == "huggingface":
        return generate_hf(
            model=model,
            prompt=prompt,
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            seed=seed,
            input_seed=input_seed,
            steps=steps,
            token=token,
        )
    if provider == "gitee":
        if not token:
            raise RuntimeError("GITEE_TOKEN environment variable required")
        return generate_gitee(
            model=model,
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            steps=steps,
            token=token,
        )
    raise RuntimeError(f"Unsupported provider: {provider}")


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate AI images via multiple providers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Providers:
  huggingface  - Free Gradio Spaces (default, no token required)
  gitee        - Gitee AI (requires GITEE_TOKEN)

HF Models:     z-image-turbo, qwen-image-fast, ovis-image
Gitee Models:  Qwen-Image, Z-Image-Turbo

Examples:
  # HF (free)
  python gen.py --prompt "a cat" --model z-image-turbo

  # Gitee AI
  python gen.py --provider gitee --model Qwen-Image --prompt "a cat"
""",
    )
    ap.add_argument("--prompt", required=True, help="Text prompt for image generation.")
    ap.add_argument(
        "--provider",
        choices=["huggingface", "hf", "gitee"],
        default="huggingface",
        help="Image generation provider (default: huggingface).",
    )
    ap.add_argument(
        "--model",
        default="z-image-turbo",
        help="Image model (default: z-image-turbo for HF).",
    )
    ap.add_argument(
        "--ratio",
        choices=list(ASPECT_RATIOS.keys()),
        default="1:1",
        help="Aspect ratio (default: 1:1).",
    )
    ap.add_argument("--hd", action="store_true", help="Enable HD mode (2x resolution).")
    ap.add_argument("--seed", type=int, help="Random seed for reproducibility.")
    ap.add_argument("--steps", type=int, help="Inference steps.")
    ap.add_argument("--out-dir", default="", help="Output directory.")
    ap.add_argument("--json", action="store_true", help="Output result as JSON.")
    args = ap.parse_args()

    provider = args.provider.lower()
    if provider == "hf":
        provider = "huggingface"
    hf_token = os.environ.get("HUGGING_FACE_TOKEN") or os.environ.get("HF_TOKEN")
    gitee_token = os.environ.get("GITEE_TOKEN")

    ratios = ASPECT_RATIOS_HD if args.hd else ASPECT_RATIOS
    width, height = ratios.get(args.ratio, (1024, 1024))
    steps = args.steps or DEFAULT_STEPS.get(args.model, 9)
    seed = args.seed if args.seed is not None else random.randint(0, 2147483647)

    result = {
        "prompt": args.prompt,
        "provider": provider,
        "model": args.model,
        "aspect_ratio": args.ratio,
        "width": width,
        "height": height,
        "seed": seed,
        "steps": steps,
        "hd": args.hd,
        "url": None,
        "local_path": None,
        "auth_mode": None,
        "final_provider": None,
        "final_model": None,
        "attempts": [],
    }

    attempts = build_attempt_plan(
        requested_provider=provider,
        requested_model=args.model,
        hf_token=hf_token,
        gitee_token=gitee_token,
    )

    if not attempts:
        result["error"] = "No available provider attempts. Check provider/model selection and tokens."
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    last_error = None

    try:
        for idx, attempt in enumerate(attempts):
            label = f"{attempt['provider']}/{attempt['model']}/{attempt['auth_mode']}"
            log(attempt["provider"], f"attempt {idx + 1}/{len(attempts)}: {label}")
            try:
                generated = run_attempt(
                    attempt=attempt,
                    prompt=args.prompt,
                    width=width,
                    height=height,
                    aspect_ratio=args.ratio,
                    seed=seed,
                    input_seed=args.seed,
                    steps=steps,
                )

                result["auth_mode"] = attempt["auth_mode"]
                result["final_provider"] = attempt["provider"]
                result["final_model"] = attempt["model"]
                result["attempts"].append({"provider": attempt["provider"], "model": attempt["model"], "auth_mode": attempt["auth_mode"], "status": "success"})

                if attempt["provider"] == "huggingface" and attempt["model"] == "qwen-image-fast" and isinstance(generated, tuple):
                    result["url"], result["seed"] = generated
                else:
                    result["url"] = generated
                break
            except Exception as e:
                last_error = e
                result["attempts"].append({
                    "provider": attempt["provider"],
                    "model": attempt["model"],
                    "auth_mode": attempt["auth_mode"],
                    "status": "failed",
                    "error": str(e),
                })
                log(attempt["provider"], f"failed: {e}")
                if idx == len(attempts) - 1:
                    raise
                if not is_retryable_error(e):
                    log(attempt["provider"], "error not marked retryable, but continuing to next provider fallback")
                continue

        if args.out_dir and result["url"]:
            out_dir = Path(args.out_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{slugify(args.prompt)}-{result['seed']}.png"
            out_path = out_dir / filename

            if result["url"].startswith("data:"):
                save_base64_image(result["url"], out_path)
            else:
                download_image(result["url"], out_path)

            result["local_path"] = str(out_path)
            if not args.json:
                print(f"Image saved to: {out_path}")

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            url_preview = result["url"][:80] + "..." if len(result["url"] or "") > 80 else result["url"]
            print(f"Generated image: {url_preview}")
            print(f"Requested: {provider}/{args.model}")
            print(f"Final: {result['final_provider']}/{result['final_model']}")
            if result.get("auth_mode"):
                print(f"Auth: {result['auth_mode']}")

        return 0

    except Exception as e:
        result["error"] = str(e if e else last_error)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())