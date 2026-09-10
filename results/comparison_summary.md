# Model comparison (run 20260910-180215, prompt v3, 80 runs)

## Accuracy against the answer key

| Model | Category | Priority | Sentiment | All three right | Valid | Needed a retry |
|---|---|---|---|---|---|---|
| llama3.2:3b | 32/40 (80%) | 26/40 (65%) | 29/40 (72%) | 15/40 (38%) | 40/40 | 0 |
| phi4-mini | 28/40 (70%) | 26/40 (65%) | 34/40 (85%) | 18/40 (45%) | 40/40 | 0 |

## Priority mix-ups

**llama3.2:3b** - rows: answer key, columns: what the model said

| Key \ Model | low | medium | high | urgent |
|---|---|---|---|---|
| low | **9** | 1 | · | · |
| medium | 5 | **5** | 1 | · |
| high | · | 4 | **8** | 2 |
| urgent | · | 1 | · | **4** |

**phi4-mini** - rows: answer key, columns: what the model said

| Key \ Model | low | medium | high | urgent |
|---|---|---|---|---|
| low | **7** | 2 | 1 | · |
| medium | 3 | **7** | 1 | · |
| high | 1 | 1 | **9** | 3 |
| urgent | · | · | 2 | **3** |

## Speed and memory (warm tickets)

| Model | Median time per ticket (s) | Slowest (s) | Median time to first token (s) | Tokens/sec | Words/sec | Cold load (s) | Memory (GB) |
|---|---|---|---|---|---|---|---|
| llama3.2:3b | 3.83 | 5.41 | 0.25 | 20.4 | 12.8 | 2.63 | 2.55 |
| phi4-mini | 5.51 | 8.27 | 0.32 | 15.8 | 9.0 | 5.46 | 3.09 |

## Blind head-to-head judging

10 tickets judged blind (answers shown as A/B in random order).

| | Better summary | Better action items |
|---|---|---|
| llama3.2:3b | 8/10 | 8/10 |
| phi4-mini | 2/10 | 2/10 |
| tie | 0/10 | 0/10 |

| Ticket | Better summary | Better action items | Judge's reason |
|---|---|---|---|
| t01 | phi4-mini | phi4-mini | Checks the billing before refunding instead of refunding without checking, even though the other answer also covered resending the invites. |
| t05 | phi4-mini | phi4-mini | Clearer summary; the action items investigate the payment issue and make sure the team has access. |
| t09 | llama3.2:3b | llama3.2:3b | Preferred overall (no specific reason given). |
| t12 | llama3.2:3b | llama3.2:3b | More understandable. |
| t17 | llama3.2:3b | llama3.2:3b | More understandable. |
| t21 | llama3.2:3b | llama3.2:3b | No specific reason given. |
| t26 | llama3.2:3b | llama3.2:3b | More understandable. |
| t28 | llama3.2:3b | llama3.2:3b | More understandable. |
| t35 | llama3.2:3b | llama3.2:3b | No specific reason given. |
| t39 | llama3.2:3b | llama3.2:3b | More understandable. |

## Every mistake

| Ticket | Model | Wrong labels (key → model) |
|---|---|---|
| t01 | llama3.2:3b | sentiment: neutral → negative |
| t02 | llama3.2:3b | sentiment: neutral → negative |
| t03 | llama3.2:3b | category: billing → account; priority: medium → low |
| t05 | llama3.2:3b | category: billing → technical |
| t06 | llama3.2:3b | category: billing → other |
| t07 | llama3.2:3b | sentiment: neutral → negative |
| t08 | llama3.2:3b | category: billing → other; priority: medium → low |
| t09 | llama3.2:3b | priority: high → urgent |
| t11 | llama3.2:3b | category: technical → other; priority: medium → low |
| t12 | llama3.2:3b | priority: medium → high |
| t14 | llama3.2:3b | category: technical → other |
| t17 | llama3.2:3b | category: technical → account; priority: urgent → medium; sentiment: neutral → negative |
| t20 | llama3.2:3b | priority: low → medium |
| t21 | llama3.2:3b | category: account → technical |
| t25 | llama3.2:3b | sentiment: neutral → negative |
| t26 | llama3.2:3b | priority: high → urgent |
| t27 | llama3.2:3b | priority: high → medium; sentiment: neutral → negative |
| t30 | llama3.2:3b | priority: high → medium; sentiment: neutral → negative |
| t32 | llama3.2:3b | priority: high → medium |
| t33 | llama3.2:3b | priority: high → medium |
| t34 | llama3.2:3b | sentiment: neutral → positive |
| t35 | llama3.2:3b | priority: medium → low |
| t37 | llama3.2:3b | sentiment: neutral → positive |
| t38 | llama3.2:3b | sentiment: neutral → negative |
| t40 | llama3.2:3b | priority: medium → low; sentiment: neutral → positive |
| t02 | phi4-mini | priority: high → urgent; sentiment: neutral → negative |
| t03 | phi4-mini | category: billing → account; priority: medium → low; sentiment: positive → neutral |
| t04 | phi4-mini | priority: high → urgent |
| t06 | phi4-mini | category: billing → account |
| t07 | phi4-mini | priority: high → urgent; sentiment: neutral → negative |
| t08 | phi4-mini | category: billing → account; priority: medium → low |
| t11 | phi4-mini | priority: medium → low |
| t12 | phi4-mini | priority: medium → high |
| t14 | phi4-mini | category: technical → other |
| t17 | phi4-mini | category: technical → account; priority: urgent → high; sentiment: neutral → negative |
| t20 | phi4-mini | priority: low → medium |
| t21 | phi4-mini | priority: urgent → high |
| t27 | phi4-mini | priority: high → medium |
| t30 | phi4-mini | sentiment: neutral → negative |
| t33 | phi4-mini | priority: high → low |
| t34 | phi4-mini | category: other → account |
| t35 | phi4-mini | category: other → account |
| t36 | phi4-mini | category: other → account |
| t37 | phi4-mini | category: other → account; priority: low → medium |
| t38 | phi4-mini | category: other → account |
| t39 | phi4-mini | category: other → account; priority: low → high |
| t40 | phi4-mini | category: other → account; sentiment: neutral → positive |
