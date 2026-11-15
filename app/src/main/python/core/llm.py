import os
import re
import time
import requests
from pathlib import Path


# Carrega a chave do arquivo .env.
env_file = Path(__file__).resolve().parent.parent / ".env"

if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(
                name.strip(),
                value.strip().strip('"').strip("'")
            )


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"

MAX_INPUT_CHARS = 6000
MAX_SYSTEM_CHARS = 3000
MAX_HISTORY_MESSAGES = 10
MAX_COMPLETION_TOKENS = 800
MAX_CONTINUATIONS = 2
MAX_RETRIES = 3
MAX_RETRY_WAIT = 60


def compact_messages(messages):
    if not messages:
        return []

    system_messages = [
        m for m in messages if m.get("role") == "system"
    ]

    other_messages = [
        m for m in messages if m.get("role") != "system"
    ]

    result = []
    used = 0

    for message in system_messages[:1]:
        content = str(message.get("content", ""))[:MAX_SYSTEM_CHARS]

        result.append({
            "role": "system",
            "content": content
        })

        used += len(content)

    remaining = max(0, MAX_INPUT_CHARS - used)

    # Mantém somente as últimas 10 mensagens da conversa.
    recent = other_messages[-MAX_HISTORY_MESSAGES:]
    selected = []

    for message in reversed(recent):
        if remaining <= 0:
            break

        role = message.get("role", "user")
        content = str(message.get("content", ""))

        if len(content) > remaining:
            content = content[-remaining:]

        if content:
            selected.append({
                "role": role,
                "content": content
            })
            remaining -= len(content)

    result.extend(reversed(selected))
    return result


def _retry_delay(response, attempt):
    headers = response.headers

    for header in (
        "Retry-After",
        "x-ratelimit-reset-tokens",
        "x-ratelimit-reset-requests"
    ):
        value = headers.get(header)

        if not value:
            continue

        match = re.search(r"(\d+(?:\.\d+)?)", value)

        if match:
            delay = float(match.group(1))

            if value.strip().lower().endswith("m"):
                delay *= 60

            return min(max(delay, 1), MAX_RETRY_WAIT)

    return min(2 ** (attempt + 1), MAX_RETRY_WAIT)


def _request_groq(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "reasoning_effort": "low",
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(MAX_RETRIES + 1):

        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=120,
            )

        except requests.exceptions.RequestException as error:
            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"Falha de conexão com a Groq: {error}"
                )

            delay = min(2 ** (attempt + 1), MAX_RETRY_WAIT)
            print(f"[GROQ] Falha de conexão. Nova tentativa em {delay}s.")
            time.sleep(delay)
            continue

        if response.status_code == 401:
            raise RuntimeError("Chave Groq inválida ou revogada.")

        if response.status_code == 429:
            try:
                data = response.json()
                details = data.get("error", {}).get("message", "")
            except (ValueError, AttributeError):
                details = response.text[:300]

            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"Limite Groq HTTP 429 após {MAX_RETRIES} tentativas: "
                    f"{details}"
                )

            delay = _retry_delay(response, attempt)

            print(
                f"[GROQ] Limite de requisições atingido. "
                f"Aguardando {delay:.1f}s."
            )

            time.sleep(delay)
            continue

        if response.status_code == 413:
            raise RuntimeError("Contexto muito grande para a Groq.")

        if response.status_code >= 500:
            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"Servidor Groq indisponível: HTTP {response.status_code}"
                )

            delay = min(2 ** (attempt + 1), MAX_RETRY_WAIT)
            print(f"[GROQ] Erro temporário HTTP {response.status_code}.")
            time.sleep(delay)
            continue

        if not response.ok:
            raise RuntimeError(
                f"Erro Groq HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        try:
            data = response.json()
            choice = data["choices"][0]
            answer = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")

            if not isinstance(answer, str):
                raise TypeError("Resposta não textual")

            return answer, finish_reason

        except (ValueError, KeyError, IndexError, TypeError):
            raise RuntimeError("A Groq retornou uma resposta inválida.")

    raise RuntimeError("Não foi possível consultar a Groq.")


def _remove_overlap(previous, new_text):
    if not previous or not new_text:
        return new_text

    limit = min(len(previous), len(new_text), 1500)

    for size in range(limit, 30, -1):
        if previous.endswith(new_text[:size]):
            return new_text[size:].lstrip()

    return new_text


def _build_continuation(messages, answer):
    system = [
        m for m in messages if m.get("role") == "system"
    ]

    history = [
        m for m in messages if m.get("role") != "system"
    ]

    result = system + history[-4:]

    result.append({
        "role": "assistant",
        "content": answer[-2500:]
    })

    result.append({
        "role": "user",
        "content": (
            "Continue a resposta anterior exatamente do ponto "
            "em que ela terminou. Não repita o conteúdo já escrito. "
            "Mantenha o idioma, o assunto e o estilo da conversa."
        )
    })

    return compact_messages(result)


def chat(messages):
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY não encontrada no arquivo .env"
        )

    safe_messages = compact_messages(messages)

    answer, finish_reason = _request_groq(safe_messages)

    attempts = 0

    while (
        finish_reason == "length"
        and attempts < MAX_CONTINUATIONS
    ):
        continuation = _build_continuation(
            safe_messages,
            answer
        )

        next_answer, finish_reason = _request_groq(
            continuation
        )

        next_answer = _remove_overlap(
            answer,
            next_answer
        )

        answer += next_answer
        attempts += 1

    return answer
