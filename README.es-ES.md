# Peinture

🎨 Skill de generación de imágenes con IA para **OpenClaw**. Genera imágenes a través de múltiples proveedores con fallback automático.

## Características

- Múltiples proveedores: Hugging Face (gratis) y Gitee AI
- Fallback automático entre proveedores
- Múltiples modelos: Z-Image-Turbo, Qwen-Image, Ovis-Image
- Soporte para relación de aspecto y modo HD
- Salida JSON para uso programático

## Instalación

Copia la carpeta `peinture` en tu directorio de skills de OpenClaw:

```bash
cp -r peinture ~/.openclaw/skills/
```

O para despliegues con Docker, móntala en tu directorio de configuración.

## Uso

### Línea de Comandos

```bash
# Uso básico (Hugging Face, gratis)
python3 scripts/gen.py --prompt "a beautiful sunset over mountains"

# Especificar modelo
python3 scripts/gen.py --prompt "cyberpunk city" --model qwen-image-fast

# Gitee AI (requiere token)
export GITEE_TOKEN=your_token_here
python3 scripts/gen.py --provider gitee --model Qwen-Image --prompt "cute cat"
```

### Integración con OpenClaw

La skill es reconocida automáticamente por OpenClaw. Solo pide a la IA que genere una imagen:

```
Generate an image of a sunset over the ocean
```

## Opciones

| Opción | Predeterminado | Descripción |
|--------|---------|-------------|
| `--prompt` | (requerido) | Prompt de texto para la generación de imagen |
| `--provider` | huggingface | Proveedor: `huggingface` o `gitee` |
| `--model` | z-image-turbo | Nombre del modelo (ver abajo) |
| `--ratio` | 1:1 | Relación de aspecto: 1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3 |
| `--hd` | false | Activa resolución 2x |
| `--seed` | random | Semilla aleatoria para reproducibilidad |
| `--steps` | default del modelo | Pasos de inferencia |
| `--out-dir` | (ninguno) | Guardar imagen en directorio |
| `--json` | false | Salida del resultado en formato JSON |

## Modelos

### Hugging Face (Gratis)

| Modelo | Descripción |
|-------|-------------|
| `z-image-turbo` | Modelo rápido de propósito general (predeterminado) |
| `qwen-image-fast` | Generación de imágenes Qwen |
| `ovis-image` | Generación de imágenes Ovis 7B |

### Gitee AI (Requiere Token)

| Modelo | Descripción |
|-------|-------------|
| `Qwen-Image` | Generación de imágenes Qwen |
| `Z-Image-Turbo` | Z-Image Turbo |

## Variables de Entorno

| Variable | Descripción |
|----------|-------------|
| `HUGGING_FACE_TOKEN` o `HF_TOKEN` | Opcional, para límites de tasa más altos en HF |
| `GITEE_TOKEN` | Requerido para Gitee AI |

## Obtención de Tokens de API

### Hugging Face (Opcional)

1. Visita https://huggingface.co/settings/tokens
2. Crea un Access Token (el permiso de Read es suficiente)
3. Configura la variable de entorno: `HUGGING_FACE_TOKEN=hf_xxx`

> Los usuarios gratuitos de Hugging Face tienen una cuota pública; puedes usarlo sin token, pero con límites de tasa más bajos.

### Gitee AI

1. Visita https://ai.gitee.com/
2. Inicia sesión y ve a Console → API Keys
3. Crea una clave y cópiala
4. Configura la variable de entorno: `GITEE_TOKEN=xxx`

## Seguridad

- Nunca escribas los tokens directamente en tu código
- Nunca subas tokens a repositorios de Git
- Usa variables de entorno para almacenar los tokens
- Para despliegues con Docker, inyéctalos mediante `environment`:

```yaml
# ejemplo de docker-compose.yml
environment:
  - HUGGING_FACE_TOKEN=${HUGGING_FACE_TOKEN}
  - GITEE_TOKEN=${GITEE_TOKEN}
```

O usa un archivo `.env` (no lo subas al repositorio):

```bash
# archivo .env
HUGGING_FACE_TOKEN=hf_your_token_here
GITEE_TOKEN=your_gitee_token
```

## Agradecimientos

Este proyecto está basado y derivado de [Amery2010/peinture](https://github.com/Amery2010/peinture). Muchas gracias al autor original por la implementación fundacional.

## Licencia

MIT
