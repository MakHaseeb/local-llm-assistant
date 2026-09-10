# Benchmark summary (run 20260910-155741, 86 runs)

## Per model

| Model | Cold load (s) | Cold TTFT (s) | Warm TTFT (s) | Cached TTFT (s) | Tokens/sec | Words/sec | Memory (GB) |
|---|---|---|---|---|---|---|---|
| llama3.2:3b | 1.11 | 1.41 / 3.17 | 0.60 / 2.02 | 0.07 / 0.10 | 20.68 / 18.64 | 17.46 / 13.15 | 2.55 |
| phi4-mini | 1.37 | 1.57 / 4.95 | 0.71 / 2.07 | 0.09 / 0.18 | 16.21 / 14.98 | 13.52 / 11.96 | 3.09 |

Times and speeds are shown as *median / worst*. Words/sec is the fairer cross-model speed, since each model counts tokens differently. Cold = model unloaded before the run. Warm = model in memory, new input each time (what a real new ticket costs). Cached = the exact same input repeated, so Ollama skips re-reading it.

## Per prompt (medians)

| Prompt | Model | Input tokens | Output tokens | Warm TTFT (s) | Cached TTFT (s) | Total (s) |
|---|---|---|---|---|---|---|
| short_classify | llama3.2:3b | 59 | 11 | 0.32 | 0.06 | 0.75 |
| short_classify | phi4-mini | 37 | 2 | 0.37 | 0.06 | 0.43 |
| medium_summary | llama3.2:3b | 121 | 68 | 0.77 | 0.07 | 3.91 |
| medium_summary | phi4-mini | 97 | 54 | 0.71 | 0.06 | 3.89 |
| medium_reply | llama3.2:3b | 100 | 116 | 0.60 | 0.09 | 6.20 |
| medium_reply | phi4-mini | 74 | 94 | 0.73 | 0.12 | 6.48 |
| long_action_items | llama3.2:3b | 287 | 171 | 1.76 | 0.10 | 10.71 |
| long_action_items | phi4-mini | 258 | 109 | 1.87 | 0.09 | 9.04 |
| open_ended | llama3.2:3b | 51 | 200 | 0.25 | 0.07 | 10.65 |
| open_ended | phi4-mini | 28 | 200 | 0.28 | 0.10 | 13.16 |
