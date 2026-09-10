# Temperature experiment (run 20260910-173236, 160 runs, prompt v2)

## Consistency across repeats

| Model | Temp | Valid | Category agree | Priority agree | Sentiment agree | Distinct answers / ticket | Summary overlap |
|---|---|---|---|---|---|---|---|
| llama3.2:3b | 0.0 | 40/40 | 100% | 100% | 100% | 1.0 | 1.00 |
| llama3.2:3b | 0.7 | 40/40 | 95% | 90% | 100% | 5.0 | 0.43 |
| phi4-mini | 0.0 | 40/40 | 100% | 100% | 100% | 1.0 | 1.00 |
| phi4-mini | 0.7 | 40/40 | 92% | 92% | 92% | 5.0 | 0.46 |

Agreement = how often a label matched that ticket's most common answer (100% = never changed). Distinct answers = different complete answers per ticket (1.0 = identical every time). Summary overlap = shared words between summaries of the same ticket (1.00 = word-for-word identical).

## Matches the answer key

| Model | Temp | Category | Priority | Sentiment |
|---|---|---|---|---|
| llama3.2:3b | 0.0 | 100% | 62% | 62% |
| llama3.2:3b | 0.7 | 95% | 57% | 62% |
| phi4-mini | 0.0 | 88% | 25% | 62% |
| phi4-mini | 0.7 | 92% | 22% | 70% |

## Every ticket (label × times given)

| Ticket | Model | Temp | Category | Priority | Sentiment | Expected |
|---|---|---|---|---|---|---|
| t01 | llama3.2:3b | 0.0 | billing×5 | high×5 | negative×5 | billing/high/neutral |
| t01 | llama3.2:3b | 0.7 | billing×5 | high×5 | negative×5 | billing/high/neutral |
| t01 | phi4-mini | 0.0 | billing×5 | high×5 | negative×5 | billing/high/neutral |
| t01 | phi4-mini | 0.7 | billing×5 | high×4 urgent×1 | negative×4 neutral×1 | billing/high/neutral |
| t02 | llama3.2:3b | 0.0 | billing×5 | high×5 | negative×5 | billing/high/neutral |
| t02 | llama3.2:3b | 0.7 | billing×5 | high×4 urgent×1 | negative×5 | billing/high/neutral |
| t02 | phi4-mini | 0.0 | billing×5 | urgent×5 | negative×5 | billing/high/neutral |
| t02 | phi4-mini | 0.7 | billing×5 | urgent×5 | negative×5 | billing/high/neutral |
| t09 | llama3.2:3b | 0.0 | technical×5 | high×5 | negative×5 | technical/medium/negative |
| t09 | llama3.2:3b | 0.7 | technical×5 | high×3 urgent×2 | negative×5 | technical/medium/negative |
| t09 | phi4-mini | 0.0 | technical×5 | urgent×5 | negative×5 | technical/medium/negative |
| t09 | phi4-mini | 0.7 | technical×5 | urgent×5 | negative×5 | technical/medium/negative |
| t13 | llama3.2:3b | 0.0 | technical×5 | urgent×5 | negative×5 | technical/urgent/negative |
| t13 | llama3.2:3b | 0.7 | technical×5 | urgent×5 | negative×5 | technical/urgent/negative |
| t13 | phi4-mini | 0.0 | technical×5 | urgent×5 | negative×5 | technical/urgent/negative |
| t13 | phi4-mini | 0.7 | technical×5 | urgent×5 | negative×5 | technical/urgent/negative |
| t21 | llama3.2:3b | 0.0 | account×5 | medium×5 | negative×5 | account/urgent/negative |
| t21 | llama3.2:3b | 0.7 | account×3 technical×2 | medium×5 | negative×5 | account/urgent/negative |
| t21 | phi4-mini | 0.0 | account×5 | high×5 | negative×5 | account/urgent/negative |
| t21 | phi4-mini | 0.7 | account×5 | high×5 | negative×5 | account/urgent/negative |
| t26 | llama3.2:3b | 0.0 | shipping×5 | urgent×5 | negative×5 | shipping/high/negative |
| t26 | llama3.2:3b | 0.7 | shipping×5 | urgent×5 | negative×5 | shipping/high/negative |
| t26 | phi4-mini | 0.0 | shipping×5 | urgent×5 | negative×5 | shipping/high/negative |
| t26 | phi4-mini | 0.7 | shipping×5 | urgent×5 | negative×5 | shipping/high/negative |
| t30 | llama3.2:3b | 0.0 | shipping×5 | medium×5 | negative×5 | shipping/medium/neutral |
| t30 | llama3.2:3b | 0.7 | shipping×5 | medium×4 high×1 | negative×5 | shipping/medium/neutral |
| t30 | phi4-mini | 0.0 | shipping×5 | urgent×5 | negative×5 | shipping/medium/neutral |
| t30 | phi4-mini | 0.7 | shipping×5 | urgent×5 | negative×3 neutral×2 | shipping/medium/neutral |
| t39 | llama3.2:3b | 0.0 | other×5 | low×5 | negative×5 | other/low/negative |
| t39 | llama3.2:3b | 0.7 | other×5 | low×5 | negative×5 | other/low/negative |
| t39 | phi4-mini | 0.0 | account×5 | urgent×5 | negative×5 | other/low/negative |
| t39 | phi4-mini | 0.7 | other×2 technical×2 account×1 | urgent×3 high×2 | negative×5 | other/low/negative |
