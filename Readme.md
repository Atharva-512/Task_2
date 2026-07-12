# Task 2 — Serve It: A Public Data Web App

## The short version
Task 1 asked whether you can **land, transform, and model** data. Task 2 asks a different question: **can you serve it?**

Instead of a drag-and-drop BI tool, build a small web application — your own backend and frontend — that exposes the analytics you produced in Task 1, and **deploy it to a public URL** we can open in a browser. This is intentionally a different muscle from a BI dashboard: it tests a data-serving/API layer, a bit of full-stack wiring, and real deployment.

You have wide latitude on *how* you build it. We care about the decisions you make and whether you can defend them — not about matching a prescribed stack.

---

## Scenario
Thepla House is a multi-brand cloud kitchen in Mumbai, running brands such as **Thepla House** and **Homely & Healthy Appetite** across Swiggy, Zomato, and direct channels. The owner doesn't want to log into a BI tool — they want to glance at a link on their phone and see how the kitchen is doing: what's selling, which platform is pulling weight, how fast the kitchen is turning orders around, and whether today looks off.

Your Task 1 pipeline already produces the clean, modelled data behind those questions. Task 2 is the thin, live, shareable surface on top of it.

---

## The data question — read this, it changes the task
Your Task 1 gold layer lives in some **queryable store** — and that's what your app reads from, **not Power BI.** Use whatever store you're comfortable with: a relational database (PostgreSQL, MySQL, SQLite), an in-process engine like DuckDB, parquet files queried directly, or a cloud warehouse (BigQuery, Snowflake). **Any of them is fine** — we don't care which you pick. The only thing that matters is that your app **queries a real data store on demand**, against your real gold-layer schema. Power BI (or any closed BI tool) is a presentation layer, not a data source; trying to pipe data back out of it is the wrong path, and the reason it feels hard. Pointing a web app at the store you already built is the normal, straightforward pattern.

Two firm rules on data:

1. **The code path must be real.** Your app queries your actual gold-layer schema — the same tables Task 1 produces. Not a hand-copied JSON of results.
2. **The public deployment must be safe.** Do **not** publish real business figures to a public URL. Seed the *deployed* instance with **schema-matching synthetic data** — a stub that mirrors your real gold schema exactly (same tables, same columns, same types; only the values are fake). So: **real query code, safe public data.** Swapping the synthetic seed for the real gold layer should be a **config change**, and you should be able to show the app running on the **real** data locally during the walkthrough.

> Example of "schema-matching synthetic data": if your gold layer has `fact_orders(order_date, brand, platform, gross_revenue, order_count)`, your synthetic seed has the exact same table and columns, populated with plausible-but-fake numbers. Your queries don't change; only the source they point at does.

*(If you genuinely cannot wire the app to your gold layer in time, a pure stub is an accepted fallback — but it is the weaker submission, and the stub must still match your real schema so the swap is trivial.)*

---

## What you'll demonstrate
- You can expose a modelled dataset through a **queryable service**, not a static file.
- You can build a **minimal, honest, usable** interface on top of it.
- You can **deploy** and keep a public URL running.
- You can reason about **refresh, safety, and what production would need** — even if you don't build all of it.

---

## Requirements

### 1. Backend / serving layer
- Reads from your **gold-layer schema** and answers analytical queries **on demand** — not a single precomputed dump served as-is.
- Exposes at least a few analytical views (see *Suggested views* below — treat them as examples, not a checklist).
- **At least one endpoint must take a parameter** (e.g. a date range, platform, or brand) and query accordingly, so we can see real query-on-demand rather than everything baked at build time.

### 2. The interface
- A frontend with a few charts and **at least one interactive control** (filter, date picker, dropdown) that triggers a **real query** to your backend — not client-side filtering of one preloaded blob.
- **Functional beats beautiful.** A clean, readable, correct interface scores far higher than a polished one built on fake or broken data.
- **Label revenue honestly.** These figures are **gross customer-facing sales, not net of platform commission** — the source data has no commission or cost fields. Label it as such; do not imply it's profit. (This is the same honesty rule as Task 1, and we check for it.)

### 3. Deployment
- **Publicly hosted**, with a **live URL that works when we open it.** Free tiers are fine and expected — Streamlit Community Cloud, Render, Railway, Fly.io, Hugging Face Spaces, Vercel + serverless, etc. Your choice; justify it in a sentence.
- Free-tier cold starts / sleep are fine — just mention it in the README if the first load is slow.

### 4. Reflecting new data
- The app should **reflect a new period when the underlying data updates** — even if that's via a manual reload or redeploy rather than automatic. Explain the refresh path in your README. (This continues Task 1's theme: the system grows as new periods arrive.)

### 5. Documentation (README)
Include:
- **Architecture** — how the app gets its data from the pipeline output (a diagram or a few sentences).
- **Run locally** — the steps to run it against your **real** gold layer.
- **Live URL** — the public link, and which data it's running on (synthetic).
- **Refresh path** — how a new period shows up in the app.
- **Productionization notes** — a short "what I'd add for production": auth, caching, scheduled refresh, monitoring, and anything you deliberately left out.

---

## Deployment & data hygiene — hard rules (graded)
- **No secrets committed.** Use environment variables / the host's secrets manager.
- **No PII and no real business figures on the public URL.** Public instance runs on synthetic data only.
- The live URL is **genuinely reachable** — we will open it, on our machines, cold.

---

## Suggested views (examples — you choose what to build)
Pick a handful that tell a coherent story; you don't need all of these, and you're welcome to add better ones:
- Sales / order **trend over time** (day or week), with a platform or brand filter.
- **Top items** by units or gross revenue for a selected period.
- **Platform / brand mix** — share of orders or revenue across Swiggy / Zomato / direct and across brands.
- **Kitchen throughput** — average prep time per item, or slowest items, from the KOT process-time data.
- **Cancellations** — rate and reasons over the selected window.

---

## Definition of done (self-check before you submit)
- [ ] The app queries the gold-layer schema (real code path), with at least one **parameterized** endpoint.
- [ ] There's an interactive control that triggers a **real query**, not client-side slicing.
- [ ] It's **deployed** and the public URL loads for someone who isn't you.
- [ ] The public instance runs on **synthetic** data; **no secrets, no PII, no real figures** are exposed.
- [ ] Revenue is labelled **gross**, consistent with Task 1.
- [ ] The README covers architecture, local run against real data, the live URL, refresh path, and productionization notes.

---

## How we grade

| Area | Weight | Strong looks like |
|---|---:|---|
| Real serving layer | 30% | Queries the gold layer on demand; a genuine parameterized endpoint |
| Deployed & reachable | 20% | Public URL loads cold, first try |
| Data correctness & honesty | 15% | Matches the pipeline; gross labelled as gross |
| Code quality & structure | 15% | Clear backend/frontend separation; readable; sensible choices |
| Deployment hygiene | 10% | No secrets, no PII, env-based config |
| Docs & communication | 10% | README explains the how and the tradeoffs |

---

## Bonus (optional — and truly optional)
Only reach for these once the core is solid, deployed, and honest. A polished bonus sitting on a broken or faked core scores *worse* than a plain core done right.

- **Make it work well on a phone — the recommended bonus.** The scenario is an owner glancing at a link on their phone, so a **fully responsive** layout that's genuinely usable on a small screen fits the brief and is the bonus we'd most like to see. Charts should reflow, controls should be tap-friendly, and nothing should require horizontal scrolling or pinch-zoom to read.
- **A native / cross-platform mobile app — a far stretch.** If you're already finished and want to show range, wrapping the same serving layer in a React Native / Flutter app (or a proper installable PWA) is welcome — but be clear-eyed: this is a large, separate effort that tests mobile-dev skills more than data engineering, so it's a "nice to see," **not** something we weight heavily. Don't sacrifice the core for it. A responsive web app that works is worth more to us than a half-finished native one.

Whichever you choose, the same data rules apply: **synthetic data on anything public, and gross labelled as gross.**

---

## What we're *not* looking for
- A beautiful UI on top of fake or broken data — we'd rather see a plain UI on a real query path.
- A static export (precomputed JSON/CSV) dressed up as an app.
- Real business figures on a public URL.
- Over-engineering — microservices, Kubernetes, elaborate auth — before the core works. Get the simple thing live first; those are stretch, not baseline.

---

## Constraints & ground rules
- **Stack:** your choice. Justify the main picks briefly.
- **Time:** no fixed limit — work at your own pace, to a standard you'd be comfortable walking us through. **Deadline is in your invitation email.**
- **AI tools:** use whatever you'd use on the job. But you must **understand and be able to defend every line** you submit — including the deployment and data-access code. "The model wrote it" is not an answer to "why does this work?"

---

## Submitting your work
- Push to this repo (or a linked second repo) with a clear README.
- Include the **live public URL** in the README (and in your reply).
- If your free-tier host sleeps, note the expected first-load delay.

## The walkthrough (30–45 min)
We'll cover Task 1 and Task 2 together. For Task 2, expect to:
- Open the live URL and walk us through it.
- Show it running on your **real** gold layer locally, and explain how the frontend gets its data.
- Make a **small live change** — e.g. add a filter or a view — so we can see how you work.

Good luck — we're looking forward to seeing what you build.
