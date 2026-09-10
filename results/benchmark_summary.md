# Benchmark summary (run 20260910-154246, 56 runs)

## Per model

| Model | Cold load (s) | Cold TTFT (s) | Warm TTFT (s) | Tokens/sec | Memory (GB) |
|---|---|---|---|---|---|
| llama3.2:3b | 1.14 | 1.43 / 2.93 | 0.07 / 1.96 | 21.34 / 15.68 | 2.55 |
| phi4-mini | 1.86 | 2.05 / 4.96 | 0.12 / 2.07 | 15.99 / 13.80 | 3.09 |

Times and tokens/sec are shown as *median / worst*. Cold = model unloaded before the run; warm = model already in memory.

## Per prompt (warm runs, medians)

| Prompt | Model | Input tokens | Output tokens | Warm TTFT (s) | Total (s) |
|---|---|---|---|---|---|
| short_classify | llama3.2:3b | 54 | 11 | 0.06 | 0.54 |
| short_classify | phi4-mini | 32 | 2 | 0.06 | 0.11 |
| medium_summary | llama3.2:3b | 116 | 74 | 0.07 | 3.52 |
| medium_summary | phi4-mini | 92 | 54 | 0.08 | 3.21 |
| medium_reply | llama3.2:3b | 95 | 106 | 0.08 | 5.25 |
| medium_reply | phi4-mini | 69 | 99 | 0.16 | 6.69 |
| long_action_items | llama3.2:3b | 282 | 200 | 0.11 | 10.97 |
| long_action_items | phi4-mini | 253 | 134 | 0.13 | 9.06 |
| open_ended | llama3.2:3b | 46 | 200 | 0.07 | 9.70 |
| open_ended | phi4-mini | 23 | 200 | 0.12 | 12.99 |
