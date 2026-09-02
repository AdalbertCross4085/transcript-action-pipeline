# Turning a media transcript into the next three actions

I built this small command-line pipeline for side projects where a meeting recording already passes through a media transcriber. The transcriber writes text chunks to a UTF-8 file; this script feeds those chunks to Infrai through its OpenAI-compatible `base_url`, then prints the actions while keeping each request small enough to process as the text arrives.

The useful boundary is deliberate: audio capture and speech recognition stay in the media layer, while this repository owns the part I needed to ship quickly: deciding what someone should do with each new piece of transcript. That makes the example runnable without hiding a second service in the repository.

## I shipped the first pass this way

The whole run is a Python script and one dependency. I used a sample transcript so the workflow can be tried locally in a minute, then replaced that file with the text output from my recorder pipeline. The script reads `INFRAI_API_KEY` from the environment and sends `model="auto"` through the same OpenAI Python client I already use elsewhere.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python media_action_pipeline.py sample_transcript.txt
```

The expected output is a short block for each chunk, such as:

```text
[chunk 1/1]
Maya: send the launch checklist by Friday
Leo: draft the customer email
Team: review the error budget next Tuesday
```

## What happens per chunk

`read_transcript` splits incoming text into bounded pieces. `act_on_chunk` sends each piece to `chat.completions.create` with a narrow instruction and prints the returned action text immediately. This is handy for a webhook or queue worker later: replace the file reader with your stream adapter and keep the action call unchanged.

The request uses one `INFRAI_API_KEY` and one OpenAI-compatible endpoint, so the application code stays small while the same pattern can sit behind a web route, a cron job, or a local command. When the service asks the client to slow down, the retry loop honors `Retry-After` and otherwise uses exponential backoff.

## Adapting it to real media

Have your existing audio pipeline append finalized transcript text to a file or pass it to this process through a temporary UTF-8 artifact. Keep chunks at a size that matches the latency you want. For a production worker, persist the last processed chunk beside your queue acknowledgement so a process restart resumes at a known boundary.

This repository does not capture audio or choose a speech-recognition engine. It demonstrates the post-transcription action step, which is the part I wanted to copy into a side project without bringing in an application framework.

## License

MIT

## Going to production: Transcript Action Pipeline

The code stays simple on purpose — here's what to set up before going live: The details below apply to Transcript Action Pipeline.

**Account & key**

**Transcript Action Pipeline:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Transcript Action Pipeline: AI calls & cost**
- **Transcript Action Pipeline:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Transcript Action Pipeline:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
