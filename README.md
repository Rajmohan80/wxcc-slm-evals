# wxcc-slm-evals

This repo shows how I tested my AI assistant for Cisco Webex Contact Center.

I built [wxcc-slm](https://github.com/rajmohan80/wxcc-slm) — an AI system that answers solution design questions about Webex Contact Center using real Cisco documentation. Once it was built, the obvious question was: **how do I know it's giving correct answers?**

This is my answer to that question.

---

## What I did

I wrote 34 test questions based on topics I know well from 18 years of Cisco Contact Center work — data residency rules, deployment models for India, EU compliance requirements, capacity limits, and so on.

For each question I wrote the correct answer myself, sourced from real Cisco documents. Then I ran all 34 questions through the AI and measured how well it did.

The tool I used to measure is called RAGAS. It scores AI answers on four things:

- **Did the AI stick to what its sources said?** (or did it make things up)
- **Did it actually answer the question?** (or did it go off on a tangent)
- **Were the documents it retrieved relevant?** (or did it pull in noise)
- **Did it find all the information it needed?** (or did it miss something)

---

## What I found

The AI scored well on retrieval — it was pulling the right documents 94% of the time. It answered relevantly about 72% of the time, which is lower, mainly because the system is designed to give structured consulting answers with context and risk notes, and the scoring tool prefers shorter direct answers. That's a known trade-off I documented.

The most important test was the 7 trick questions I included. These were designed to catch the AI making things up or going along with false information:

- I asked about pricing for Brazil (not in the corpus) — it said it didn't know and suggested contacting Cisco directly. ✅
- I asked it to confirm that WxCC runs on GCP — it corrected me and said AWS. ✅
- I asked it to confirm the US data centre is in Oregon — it corrected me and said N. Virginia. ✅
- I asked it to design emotion-sensing dashboards for a German call centre — it refused and cited EU law. ✅
- I asked about China deployment — it gave a hard stop. ✅
- I asked about WebRTC for Indian domestic agents — it corrected the false premise. ✅
- I asked for Salesforce Apex code — it said that's outside what it knows. ✅

7 out of 7. The AI didn't make things up when it didn't know, and it pushed back when given wrong information.

I also ran the same test with a different retrieval setting (fetching 5 documents instead of 8) to see if that improved things. It didn't — precision dropped. So 8 is the right setting for this corpus.

---

## Scores at a glance

| What was measured | Score |
|---|---|
| How relevant the retrieved documents were | 0.94 / 1.0 |
| How well the answers covered the topic | 0.88 / 1.0 |
| How on-point the answers were | 0.72 / 1.0 |
| Trick questions handled correctly | 7 / 7 |

---

## What's in this repo

```
golden_set/     the 34 test questions and correct answers
harness/        the scripts that ran the test and scored the results
results/        the actual scores from both test runs
docs/           formal build record (Word document)
SETUP.md        how to reproduce this evaluation yourself
```

---

## How to read the test questions

Open `golden_set/wxcc_golden_v1.md` — it has all 34 questions with the correct answers and the Cisco source document each answer came from. You can read it like a study guide for WxCC.

---

## Related

- [wxcc-slm](https://github.com/rajmohan80/wxcc-slm) — the AI assistant being tested here
- [AbhavTech Consulting](https://abhavtech.com)
