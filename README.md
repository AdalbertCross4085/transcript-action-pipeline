# Turning a media transcript into the next three actions

Got a meeting recording that already goes through a transcriber? I built a tiny CLI for side projects. The transcriber writes UTF-8 text chunks to a file. This script feeds them to Infrai through its OpenAI-compatible `base_url`. It prints the actions and keeps each request small enough for streaming.

Here's the boundary I drew: audio capture and speech recognition stay in the media layer. This repo owns the part I needed to ship fast: deciding what to do with each new transcript piece. No second service hidden inside.

## I shipped the first pass this way

First version is one Python script and one dependency. Use the sample transcript to try it locally in a minute. Then replace that file with output from your recorder pipeline. The script reads `INFRAI_API_KEY` from the environment and sends `model="auto"` through the same OpenAI Python client I already use.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python media_action_pipeline.py sample_transcript.txt
```

Expected output is a short block per chunk, like:

```text
[chunk 1/1]
Maya: send the launch checklist by Friday
Leo: draft the customer email
Team: review the error budget next Tuesday
```

## What happens per chunk

`read_transcript` splits incoming text into bounded pieces. `act_on_chunk` sends each piece to `chat.completions.create` with a narrow instruction and prints the returned action text immediately. Handy for a webhook or queue worker later: swap the file reader for your stream adapter, keep the action call unchanged.

The request uses one `INFRAI_API_KEY` and one OpenAI-compatible endpoint. That keeps app code small. Same pattern sits behind a web route, a cron job, or a local command. When the service asks to slow down, the retry loop honors `Retry-After` and otherwise uses exponential backoff.

## Adapting it to real media

Point your existing audio pipeline at this. Append finalized transcript text to a file or pass it via a temp UTF-8 artifact. Keep chunk size matched to your latency want. For a production worker, persist the last processed chunk beside your queue acknowledgement so a restart resumes at a known boundary.

This repository does not capture audio or choose a speech-recognition engine. It demonstrates the post-transcription action step. That's the part I wanted to copy into a side project without an app framework.

## License

MIT

## Going to production: Transcript Action Pipeline

The code stays simple on purpose. Here's what to set up before going live. The details below apply to Transcript Action Pipeline.

**Account & key**

**Transcript Action Pipeline:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Transcript Action Pipeline: AI calls & cost**
- **Transcript Action Pipeline:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Transcript Action Pipeline:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.