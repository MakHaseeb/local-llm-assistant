# Local LLM Assistant

An AI assistant for customer support tickets that runs **entirely offline** on
a laptop, using small open-source language models through
[Ollama](https://ollama.com). No data leaves the machine.

This is the third project in a series, after
[fastapi-rag](https://github.com/MakHaseeb/fastapi-rag) and
[pitch-evaluator](https://github.com/MakHaseeb/pitch-evaluator). Both of those
call a cloud API; this one asks what it costs to stop doing that.

## Why run a model locally?

Calling a cloud API is the easy default, but it isn't always allowed or
practical:

- **Privacy.** Support tickets are full of names, emails, order numbers and
  account details. Many organizations can't send that to a third party.
- **Latency.** No network round trip.
- **Cost at scale.** No per-request bill, only the hardware you already own.
- **No internet required.** Works on a plane, in a factory, at the edge.

The trade-off is that you're limited to small models your hardware can hold,
and you inherit problems a cloud API hides from you: loading time, memory
pressure, and speed that depends on your laptop. Measuring those trade-offs is
the point of this project.

## The hardware

Every number in this README comes from one machine, which matters a lot for
local inference:

| | |
|---|---|
| Chip | Apple A18 Pro (CPU and GPU share one pool of memory) |
| RAM | **8 GB**, deliberately modest |
| Ollama | 0.34.0 |
| Models | `llama3.2:3b` (2.0 GB download), `phi4-mini` (2.5 GB download) |

8 GB rules out 7B models in practice: macOS and everyday apps already use 3-4
GB, leaving too little room without the Mac falling back to disk. The project
was scoped to two ~3-4B models for that reason.

## Setup (one time)

1. Install Ollama from [ollama.com](https://ollama.com) and open it once.
2. Download the models:
   ```bash
   ollama pull llama3.2:3b
   ollama pull phi4-mini
   ```
3. Create a virtual environment and install the Python packages:
   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

## Run it

```bash
.venv/bin/python hello_model.py              # one prompt, with timings
.venv/bin/python benchmark.py                # full Phase 1 benchmark (~10 min)
.venv/bin/python summarize.py                # tables from the latest benchmark run
.venv/bin/python triage.py "I was charged twice this month."   # ticket -> validated JSON
.venv/bin/python -m unittest discover -s tests -v              # retry-logic tests, no model needed
.venv/bin/python temperature_test.py         # temperature 0 vs 0.7 (~20 min)
.venv/bin/python summarize_temperature.py    # tables from the latest temperature run
```

## How it's put together

```
llm_client.py                  the ONE place that talks to Ollama: streams a reply,
                               records timings, unloads a model, reads its memory use
hello_model.py                 first experiment - one prompt, printed timings
benchmark.py                   Phase 1: cold / warm / cached runs, raw rows saved
summarize.py                   turns raw rows into median / worst-case tables
prompts/benchmark_prompts.json 5 support-ticket prompts - plain data, no logic
results/benchmark.jsonl        every run ever recorded, one JSON line each
results/benchmark_summary.md   latest summary tables

schemas.py                     Phase 2: what a valid triage answer looks like (Pydantic)
prompts.py                     Phase 2: versioned triage instructions - what each field means
triage.py                      Phase 2: ask -> validate -> retry once -> fail cleanly
tests/test_triage.py           7 tests of the retry logic, using a fake model
data/eval_tickets.json         40 tickets with reviewed answer-key labels (Phases 2-3)
temperature_test.py            Phase 2: same tickets, 5 repeats at temperature 0 and 0.7
summarize_temperature.py       consistency + answer-key tables from the temperature runs
```

Two decisions worth calling out:

**One client, shared by everything.** The benchmark, and later the JSON
validation and model comparison, all call the same `generate()` function. If
each script timed things its own way, comparisons between models or phases
wouldn't be fair.

**Raw data first, analysis later.** Every single run is saved the moment it
finishes. The tables are built from that file, so the analysis can change
without re-running the benchmark. That's how the words-per-second column below
was added after the fact.

## Phase 1: Benchmarks (done)

### What's measured

- **Time to first token (TTFT):** how long until the first word appears. This
  is what makes an assistant *feel* fast or slow.
- **Tokens per second:** how fast text streams once it starts.
- **Words per second:** the same speed measured in words. Each model splits
  text into tokens differently, so this is a check on the comparison between
  models.
- **Total latency:** from pressing Enter to the last word.
- **Memory:** how much RAM the model occupies while loaded.

Each measurement is taken under three conditions:

| Run type | What it means |
|---|---|
| **Cold** | The model is unloaded first, so the run includes loading it into memory. |
| **Warm** | The model is already loaded, and the input is new. This is what a real new ticket costs. |
| **Cached** | The exact same input is sent again, so Ollama can skip re-reading it. |

Settings are identical for every run: temperature 0, fixed seed, and a
200-token cap on the answer. Per model, that's 3 cold runs, 25 warm runs
(5 prompts × 5), and 15 cached runs (5 prompts × 3): 86 runs in total.
Results are reported as **median / worst**. The median is the typical run and
can't be dragged around by one slow outlier. The worst case is what an unlucky
user sees.

### Results

Run `20260910-155741`:

| Model | Cold load (s) | Cold TTFT (s) | Warm TTFT (s) | Cached TTFT (s) | Tokens/sec | Words/sec | Memory (GB) |
|---|---|---|---|---|---|---|---|
| llama3.2:3b | 1.11 | 1.41 / 3.17 | 0.60 / 2.02 | 0.07 / 0.10 | 20.68 / 18.64 | 17.46 / 13.15 | 2.55 |
| phi4-mini | 1.37 | 1.57 / 4.95 | 0.71 / 2.07 | 0.09 / 0.18 | 16.21 / 14.98 | 13.52 / 11.96 | 3.09 |

*Median / worst. For speeds, "worst" is the lowest.*

Per prompt (medians):

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

### What the numbers say

**1. Cold start dominates everything.** On the very first load after
downloading, the first answer took **~54 seconds**, almost all of it spent
loading the model. Once loaded, a new ticket's first word arrives in
**0.6-0.7 seconds**. Ollama keeps a model in memory for 5 minutes after use for
exactly this reason: holding ~3 GB of RAM is the price of not making the next
user wait a minute.

There are also two kinds of "cold". The cold loads in the table (~1.1-1.4 s)
happened while macOS still had the model file cached from recent use. The
~45-second load only happens when the file really has to come off the disk,
such as the first request after a reboot. A benchmark that only ever measures
the cached kind will badly underestimate the real worst case.

**2. My first benchmark was measuring the cache, not the model.** The first
full run repeated each prompt word for word, and the median warm time to first
token looked excellent: **0.07 s**. The raw data showed why. Only the first
repeat of each prompt actually read the input (1.80 s for the long ticket).
Repeats 2-5 took 0.05 s, because Ollama reuses its notes on text it has
already read (its **KV cache**) when a new input starts with the same text.
Real tickets are never identical, so that number was wrong. The honest median
is **0.60 s**.

The fix: warm runs now begin with a unique ticket number, which forces a full
read, and a separate **cached** run type measures the saving on purpose. On
the long ticket that's **1.76 s → 0.10 s**, about 17× faster. The saving is
real and useful: in Phase 2, every request will start with the same fixed
instructions, and the cache means those only get read once. The flawed run is
kept in `results/benchmark.jsonl` (run `20260910-154246`) as evidence.

**3. Longer input, longer wait.** The model has to read the whole input
before it can write a word. A one-line message took ~0.3 s to the first word;
a ~280-token ticket took ~1.8 s, for both models.

**4. Llama is faster and lighter, by either measure.** `llama3.2:3b` writes
about **28% faster** in tokens per second and **29% faster** in words per
second, and uses 0.5 GB less memory (2.55 vs 3.09 GB). An early single test
had suggested Phi was faster, which is why every measurement here is repeated.

I added words per second because the two models count tokens very
differently. The same one-line message is 59 tokens to Llama and 37 to Phi,
partly because Llama adds a hidden header to every chat. I expected this to
change the speed comparison. On the flawed first run, it did (the gap looked
like 21% instead of 33%). On the final run, both measures agree. So the token
difference matters for how much input fits in a model's memory, but not for
which model is faster.

**5. Speed isn't the same as finishing first.** On the long ticket, the
"slower" Phi finished in **9.0 s** and Llama in **10.7 s**, because Phi wrote a
shorter answer (109 vs 171 tokens). Asked to reply with one word, Phi used 2
tokens and Llama 11. Only when both hit the 200-token cap (the open-ended
prompt) does raw speed decide: Llama 10.7 s, Phi 13.2 s. How long a model
tends to talk matters as much as how fast it talks. Whether the shorter
answers are also *good* answers is a question for Phase 3.

### Known limits

- **One machine.** These numbers describe an 8 GB Apple laptop, not local
  inference in general.
- **The ~45 s truly-cold load was measured once per model**, on day one, not
  repeated under controlled conditions.
- **Background activity matters.** macOS isn't a lab. The worst-case column
  is where that shows up.
- **Five prompts.** Enough to see the patterns in speed, not to judge
  quality. Quality is Phase 3's job, with 30-50 prompts.

## Phase 2: Structured output (done)

A free-text answer is fine for a person to read, but a support system needs
to route tickets automatically, so the answer has to be data with a fixed
shape:

```json
{
  "category": "billing | technical | account | shipping | other",
  "priority": "low | medium | high | urgent",
  "sentiment": "negative | neutral | positive",
  "summary": "one or two sentences",
  "action_items": ["1 to 8 concrete steps"]
}
```

### The pattern: constrain, validate, retry

1. **Constrain.** The schema is handed to Ollama, which only lets the model
   produce text that fits that shape.
2. **Validate.** Pydantic (`schemas.py`) checks every answer anyway: allowed
   values only, summary length, 1-8 action items, no extra fields. Nothing
   the model says is trusted until it passes.
3. **Retry once.** If an answer is rejected, the model is shown its reply and
   the exact reasons, and asked again. If the reply wasn't readable JSON at
   all, a plain-English hint is added, because Pydantic's message for that
   case ("expected value at line 1 column 1") is written for programmers,
   not models.
4. **Fail cleanly.** After two failures, `triage()` returns a failure with
   every reply and error kept, meaning "this ticket needs a human", instead
   of crashing.

The schema controls the *shape*; the instructions in `prompts.py` control
the *meaning*. The model never sees the schema itself, so the instructions
are where it learns what "urgent" or "account" means. They're versioned, so
every result can be traced back to the exact wording that produced it.

The retry logic is covered by 7 unit tests (`tests/test_triage.py`) that
swap the model for a fake with scripted replies: valid first time, wrong then
right, wrong twice. A real model can't be made to fail on demand, and with
the schema on, it never did.

### Findings so far

**1. You can't check "correct" until you've defined it.** With the first
version of the instructions, the two models disagreed on 2 of 3 tickets:

| Ticket | llama3.2:3b | phi4-mini |
|---|---|---|
| Can't log in since an app update | account | technical |
| Five problems in one ticket | account | billing |

Neither was wrong. The definitions were ambiguous: logging in was listed
under *account*, bugs under *technical*, and a five-issue ticket fits no
single category. Version 2 added two tie-break rules: a login broken by a
bug is **technical**, and a multi-issue ticket takes the category of its
**most serious** issue (money first, then broken things). Both models then
agreed on all three. Those rules also become the answer key for Phase 3's
scoring.

**2. Instructions ask; constraints enforce.**

| | Schema on | Schema off |
|---|---|---|
| llama3.2:3b | 6/6 valid | 3/3 valid, first try |
| phi4-mini | 6/6 valid | **0 of 18 replies valid** |

Without the schema, `phi4-mini` wraps its JSON in markdown marks
(` ```json ... ``` `), which isn't valid JSON. Everything tried to prompt
this away failed, every time:

- a retry with Pydantic's error message
- a retry with a plain-English hint ("no ``` marks")
- a retry that hid its bad reply, in case it was copying itself
- the "no ``` marks" rule in the instructions from the very first request

It's a habit from the model's training, and at temperature 0 it's
completely consistent. The takeaway: the retry is a **safety net for
occasional slips** (a wrong category, a missing field), not a fix for a
habit a model has every single time. Where a hard guarantee is available,
use it. Here that means constrained generation stays on by default.

**3. The Phase 1 cache finding pays off.** Every request starts with the
same ~250 tokens of instructions, followed by the ticket. After the first
ticket, the instructions are already cached. The next ticket's reading time
dropped from 1.38 s to 0.33 s, because only the new ticket had to be read.

### Temperature: 0 vs 0.7

Temperature controls randomness. At 0 the model always picks its most likely
next word; at 0.7 it sometimes picks a less likely one. To measure the
effect, 8 tickets (a mix of clear-cut and deliberately ambiguous) were each
triaged 5 times at each temperature, by both models: 160 runs, schema on,
prompt v2. There was **no fixed seed**, since a seed would make even 0.7
repeat itself exactly.

| Model | Temp | Valid | Category unchanged | Priority unchanged | Sentiment unchanged | Different answers per 5 repeats | Words shared between summaries |
|---|---|---|---|---|---|---|---|
| llama3.2:3b | 0.0 | 40/40 | 100% | 100% | 100% | 1.0 | 100% |
| llama3.2:3b | 0.7 | 40/40 | 95% | 90% | 100% | 5.0 | 43% |
| phi4-mini | 0.0 | 40/40 | 100% | 100% | 100% | 1.0 | 100% |
| phi4-mini | 0.7 | 40/40 | 92% | 92% | 92% | 5.0 | 46% |

*"Unchanged" = how often a label matched that ticket's most common answer.
Full per-ticket results: `results/temperature_summary.md`.*

**1. Temperature 0 was perfectly repeatable, without a seed.** All 80 runs at
temperature 0 matched word for word within each ticket. My previous
project, pitch-evaluator, notes that temperature 0 *isn't* deterministic on a
cloud API. One common explanation is that cloud providers process many
users' requests together in batches, which slightly changes the arithmetic
from one request to the next. A laptop handling one request at a time
doesn't have that source of variation. Caveat: 5 repeats, one machine.

**2. At 0.7 the wording changes every time; the labels mostly don't.** Every
repeat was a different answer, and summaries of the same ticket shared less
than half their words. But labels held 90-95% of the time.

**3. Randomness hits the unclear tickets.** The clear-cut ticket (an API
down, losing sales every minute) never changed a label in 10 runs at 0.7.
The changes came on exactly the tickets where the rules had gaps:

- a security scare: Llama said *account* 3 times and *technical* 2 times
- an angry ticket with nothing broken: Phi gave 3 different categories in 5 runs
- tickets with deadlines: priority flipped

Temperature 0 hides that uncertainty rather than removing it, so running
at 0.7 is a cheap way to find where the instructions are unclear.

**4. 0.7 didn't make answers more correct** (next table). For triage,
where the same ticket should always get the same label, temperature 0 is the
right setting. Higher temperatures suit tasks where variety is the point,
like drafting several possible replies.

| Model | Temp | Category correct | Priority correct | Sentiment correct |
|---|---|---|---|---|
| llama3.2:3b | 0.0 | 100% | 62% | 62% |
| llama3.2:3b | 0.7 | 95% | 57% | 62% |
| phi4-mini | 0.0 | 88% | 25% | 62% |
| phi4-mini | 0.7 | 92% | 22% | 70% |

*Against the answer key as drafted before review, with prompt v2. Phase 3
re-measures on all 40 tickets with the reviewed key and prompt v3.*

**5. A preview of Phase 3: priority is the weak spot.** Phi called 6 of the
8 tickets urgent, where the answer key has 2, including an angry ticket
where nothing is broken (5 times out of 5). Llama rated a suspected account
break-in only *medium*. Both models called politely reported problems
"negative".

### Answer-key review → prompt v3

The 40-ticket answer key in `data/eval_tickets.json` was drafted, then
reviewed rule by rule rather than ticket by ticket, because one rule settles
many tickets. Each decision went into **both** the answer key and the
instructions (prompt v3). Otherwise the models would be marked wrong for
breaking rules they were never told:

- **Deadlines.** A real deadline in the next few days raises a ticket to
  *high* even when the customer isn't blocked. *Urgent* still needs both.
- **Security.** Signs of a break-in are *urgent*; removing a former
  employee's access is *high*.
- **Minor bugs.** A cosmetic bug that doesn't stop anyone working is *low*.
- **Requests vs questions.** A request that needs the team to act is
  *medium*; an information question or feedback is *low*.
- **Anger.** Angry wording alone doesn't raise priority.
- **Sentiment is tone, not situation.** A polite report of a problem is
  *neutral*.

The review changed 4 labels (all medium → high under the deadline and
security rules) and confirmed the rest.

## Phase 3: Model comparison (planned)

Both models run on the same 40 tickets (`data/eval_tickets.json`, answer key
already reviewed), compared on speed, memory, and output quality. Quality is
scored automatically where there's a correct answer (category, priority,
sentiment, valid JSON) and by hand with a rubric where there isn't (summary
and action-item quality).
