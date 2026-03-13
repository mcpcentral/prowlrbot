# Provider Configuration Guide

ProwlrBot supports 11 built-in providers and unlimited custom OpenAI-compatible providers. The SmartRouter automatically scores and selects the best available provider.

---

## Built-in providers

| Provider ID | Name | Cost tier | Auto-detected via |
|-------------|------|-----------|------------------|
| `openai` | OpenAI | premium | `OPENAI_API_KEY` |
| `anthropic` | Anthropic | premium | `ANTHROPIC_API_KEY` |
| `groq` | Groq | low | `GROQ_API_KEY` |
| `ollama` | Ollama (local) | free | Running on `http://localhost:11434` |
| `llamacpp` | llama.cpp (local) | free | Manual download |
| `mlx` | MLX — Apple Silicon (local) | free | Manual download |
| `azure-openai` | Azure OpenAI | premium | `AZURE_OPENAI_API_KEY` |
| `zai` | Z.ai (Zhipu) | standard | `ZHIPUAI_API_KEY` |
| `dashscope` | DashScope (Alibaba) | standard | `DASHSCOPE_API_KEY` |
| `modelscope` | ModelScope | standard | `MODELSCOPE_API_KEY` |
| `aliyun-codingplan` | Aliyun Coding Plan | low | `ALIYUN_CODINGPLAN_API_KEY` |

---

## Quick setup: most common providers

### OpenAI

```bash
prowlr env set OPENAI_API_KEY sk-...
prowlr models set-llm   # pick provider=openai, model=gpt-4o or gpt-4.1
```

Available models: `gpt-5.2`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `o3`, `o4-mini`, `gpt-4o`, `gpt-4o-mini`.

### Anthropic

```bash
prowlr env set ANTHROPIC_API_KEY sk-ant-...
prowlr models set-llm   # pick provider=anthropic
```

Available models: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-5-20250514`.

### Groq (fast, cheap)

```bash
prowlr env set GROQ_API_KEY gsk_...
prowlr models set-llm
```

Available models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`, `gemma2-9b-it`.

### Ollama (local, no cloud)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull mistral:7b
# or via prowlr:
prowlr models ollama-pull mistral:7b
prowlr models ollama-pull qwen2.5:3b

# ProwlrBot auto-detects Ollama at http://localhost:11434
prowlr models set-llm   # pick provider=ollama, select the model
```

Ollama models are managed with `ollama pull`/`ollama rm` or `prowlr models ollama-pull`/`prowlr models ollama-remove`. Do not use `prowlr models add-model ollama` — Ollama refreshes its model list automatically from the Ollama daemon.

---

## Interactive full setup

```bash
prowlr models config
```

This runs a wizard: configure provider → add models → activate LLM slot. Use this for first-time setup.

---

## Checking what's configured

```bash
prowlr models list
```

Output shows each provider's base URL, API key (masked), models, and the active LLM slot.

---

## Setting the active model

The "active LLM slot" determines which provider and model ProwlrBot uses for all agent queries.

```bash
prowlr models set-llm
```

This prompts you to select from configured (API key set) providers and their model lists.

---

## Azure OpenAI

Azure requires a custom base URL (your Azure resource endpoint):

```bash
prowlr models config-key azure-openai
# When prompted for Base URL, enter:
# https://<resource-name>.openai.azure.com/openai/v1

prowlr env set AZURE_OPENAI_API_KEY your_azure_key
prowlr models set-llm   # pick azure-openai
```

---

## Local models: llama.cpp

llama.cpp runs GGUF-format models locally.

### Install dependencies

```bash
pip install 'prowlrbot[local]'
```

### Download a model

```bash
prowlr models download TheBloke/Mistral-7B-Instruct-v0.2-GGUF
# With a specific quantization file:
prowlr models download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
    -f mistral-7b-instruct-v0.2.Q4_K_M.gguf
# From ModelScope:
prowlr models download Qwen/Qwen2-0.5B-Instruct-GGUF --source modelscope
```

### Activate

```bash
prowlr models set-llm   # pick llamacpp, then your downloaded model
```

### List downloaded models

```bash
prowlr models local
prowlr models local -b llamacpp
prowlr models remove-local MODEL_ID -y
```

---

## Local models: MLX (Apple Silicon)

MLX runs models natively on Apple Silicon with Metal acceleration.

```bash
pip install 'prowlrbot[local]'
prowlr models download Qwen/Qwen2-0.5B-Instruct-GGUF -b mlx
prowlr models set-llm   # pick mlx
```

---

## Adding models to a provider

Built-in providers ship with curated model lists. You can add any model that the provider supports:

```bash
prowlr models add-model openai --model-id gpt-5-mini --model-name "GPT-5 Mini"
prowlr models add-model groq --model-id llama-3.2-90b-text-preview --model-name "Llama 3.2 90B"
prowlr models remove-model openai --model-id gpt-5-mini
```

---

## Custom providers

For any OpenAI-compatible endpoint (LM Studio, LocalAI, vLLM, Together.ai, Fireworks, etc.):

```bash
prowlr models add-provider my-vllm -n "My vLLM" -u http://localhost:8000/v1
prowlr models add-model my-vllm --model-id meta-llama/Llama-3.1-8B-Instruct \
    --model-name "Llama 3.1 8B"
prowlr models config-key my-vllm   # set API key (can be empty for local)
prowlr models set-llm              # pick my-vllm
```

Or add the custom provider in `~/.prowlrbot/providers.json`:

```json
{
  "custom_providers": {
    "my-vllm": {
      "id": "my-vllm",
      "name": "My vLLM",
      "default_base_url": "http://localhost:8000/v1",
      "api_key_prefix": "",
      "models": [
        {"id": "meta-llama/Llama-3.1-8B-Instruct", "name": "Llama 3.1 8B"}
      ]
    }
  }
}
```

---

## SmartRouter: how providers are selected

At startup, ProwlrBot runs `ProviderDetector` → `HealthChecker` → `SmartRouter`.

```
score = w_cost * cost_score + w_perf * perf_score + w_avail * avail_score
```

- `cost_tier`: `free` > `low` > `standard` > `premium` (lower cost = higher score)
- `perf_score`: measured from health check latency
- `avail_score`: 1 if reachable, 0 if health check failed

The highest-scoring provider becomes the primary. If a query fails, the fallback chain tries the next in order.

To force a specific provider, just set it as the active LLM with `prowlr models set-llm`.

---

## Environment variables reference

| Variable | Provider |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `GROQ_API_KEY` | Groq |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI |
| `ZHIPUAI_API_KEY` | Z.ai (Zhipu) |
| `DASHSCOPE_API_KEY` | DashScope |
| `MODELSCOPE_API_KEY` | ModelScope |
| `ALIYUN_CODINGPLAN_API_KEY` | Aliyun Coding Plan |

Set these with `prowlr env set KEY value` — they are stored in `~/.prowlrbot.secret/envs.json` and automatically injected at startup.

---

## Provider config file location

Provider settings (not secrets) are stored in `~/.prowlrbot/providers.json`. This file is auto-created by the CLI and should not be edited manually unless you need to add custom providers in bulk.

Secrets (API keys) are stored separately in `~/.prowlrbot.secret/envs.json` (mode 0o600).
