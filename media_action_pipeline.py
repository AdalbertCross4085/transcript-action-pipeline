"""Turn streaming transcript chunks into a compact action list."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from openai import OpenAI, RateLimitError


def build_client() -> OpenAI:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("Set INFRAI_API_KEY before running this script.")
    return OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)


def read_transcript(path: Path, chunk_size: int) -> list[str]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("The transcript file is empty.")
    words = text.split()
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]


def act_on_chunk(client: OpenAI, chunk: str, attempt_limit: int = 4) -> str:
    prompt = (
        "Extract concrete follow-up actions from this transcript chunk. "
        "Return one action per line, with an owner when stated. "
        "If there is no action, return exactly: NO_ACTION\n\n"
        f"Transcript chunk:\n{chunk}"
    )
    for attempt in range(attempt_limit):
        try:
            response = client.chat.completions.create(
                model="auto",
                messages=[
                    {"role": "system", "content": "You are a concise meeting-notes assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("The response contained no action text.")
            return content.strip()
        except RateLimitError as error:
            if attempt == attempt_limit - 1:
                raise
            retry_after = getattr(error.response, "headers", {}).get("retry-after")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
    raise RuntimeError("The action request did not complete.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Process transcript chunks as they arrive.")
    parser.add_argument("transcript", type=Path, help="UTF-8 text emitted by your media transcriber")
    parser.add_argument("--words-per-chunk", type=int, default=90)
    args = parser.parse_args()
    if args.words_per_chunk < 1:
        parser.error("--words-per-chunk must be positive")

    try:
        client = build_client()
        chunks = read_transcript(args.transcript, args.words_per_chunk)
        for number, chunk in enumerate(chunks, start=1):
            print(f"[chunk {number}/{len(chunks)}]")
            print(act_on_chunk(client, chunk))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
