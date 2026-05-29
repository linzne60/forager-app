# Forager

I wanted to build something that could tell me whether the mushroom I just found would make a good dinner or send me to the hospital. So I built a full-stack foraging assistant. Take a photo of plant or mushroom, and find out if it's edible or not, how to prepare it, nutrition info, and the weather at the time of discovery. This info streams in as the pipeline works.

Check it live **[forager.lindsayschwartz.com](https://forager.lindsayschwartz.com)**

## See It In Action

![Identification flow](docs/demo/identify-flow.gif)
*Upload a photo -> ONNX inference returns a species ID in about a second -> safety, nutrition, and weather stream in via SSE as each pipeline stage completes.*

![Discovery detail](docs/demo/discovery-detail.gif)
*CAM heatmap shows what the model focused on. Safety verdicts come from curated static data, not an LLM — no hallucination risk.*

![Journal](docs/demo/journal.gif)
*Discoveries persist progressively, even if the weather API fails, you keep everything that succeeded.*

**[forager.lindsayschwartz.com](https://forager.lindsayschwartz.com)**

## What It Does

Here's how it works, you upload a photo and confirm your location. The image hits an EfficientNet-B7 model running ONNX inference. Classification comes back in about a second with a confidence rating and a heatmap showing exactly what the model keyed in on. While you're looking at that, the rest of the pipeline is already working. Safety analysis pulls from a curated dataset covering all 105 species; toxic lookalikes, protection status by state, and preparation requirements. Then nutrition and local weather comes in. Everything streams to the client as it completes via server-sent events, so you're not waiting for everything to complete.

The safety system is the part I'm most deliberate about. There's no LLM generating safety advice. Every verdict comes from sourced, reviewed data, and the system is wired to default to "caution" if anything is uncertain, meaning low confidence, missing data, or a pipeline failure. A code path cannot produce a "safe" verdict without the data to back it up.

The species are focused on the Eastern United States and Southern Appalachian region, which includes 70 plants and 35 fungi selected for regional foraging relevance. This includes dangerous lookalikes.

An account is not required to identify a plant. But you can sign in if you want to save discoveries to a journal with notes, location, and get the nutrition information. There's also a trip planning feature to save your favorite foraging locations. You can pin the ones you visit most, and check weather forecasts before heading out.

## Technical Highlights

- **Immediate Classification:** ONNX Runtime inference, there is no PyTorch in production. A dual-output model produces both predictions and spatial feature maps for CAM heatmaps in a single forward pass.
- **Three-phase training pipeline:** Head-only warmup, full fine-tune with Mixup/CutMix augmentation, then a Phase C pass that targets the model's worst confusion pairs. The model achieved 95.7% validation accuracy across 101 classes and was trained on 177k images from iNaturalist.
- **Progressive SSE streaming:** Results stream to the client as each pipeline stage completes. The frontend navigates on classification (~1s) and fills in enrichment data as it arrives. Confidence tiers gate how much data gets sent, a weak match doesn't trigger nutrition lookups.
- **Deterministic safety pipeline:** Verdicts come from curated, sourced data covering 105 species with confidence gates and toxic lookalike checks instead of an LLM to provide instant and reproducible information.
- **Async generator orchestrator:** The pipeline is a single async generator that the SSE endpoint consumes via `async for`. Each `yield` becomes a server-sent event, with clean separation between pipeline logic and transport.
- **Progressive DB persistence:** Discoveries save on classification and update as each enrichment step completes. If the weather API goes down, everything else was save, so no data lost.
- **Rate limiting:** Redis-backed rate limiting via slowapi. Identification is capped at 10/hour, login at 5/minute, and registration at 3/minute. Limits are per-IP and survive server restarts.
- **Infrastructure as code:** Terraform for EC2, S3, and security groups. Docker Compose for the full stack.

## Design Decisions

A few choices that shaped the project, and the problems that led to them:

**The model went through a few generations.** The first attempt was using EfficientNet-B3 with 50 images per class, which hit 70.9% accuracy with severe overfitting (99% train vs 71% val). Scaling to 177k iNaturalist images and upgrading to B7 with six regularization techniques got it to 95.7%. The remaining errors are between safe species (red vs white mulberry, black walnut vs butternut), so they don't create dangerous misidentifications.

**The safety pipeline used to have an LLM in it.** The original design ran safety data through an LLM to generate verdicts. In practice, the LLM was just reading curated JSON and repeating it back — adding seconds of latency for zero value, and risking OOM on a t3.medium. I ripped it out and went fully static. Safety is now instant, deterministic, and works offline.

**The orchestrator used to be a LangGraph state machine.** LangGraph is great for complex branching workflows, but this pipeline is essentially linear with one branch (nutrition is gated on confidence tier). An async generator is simpler, naturally supports `async for` streaming, and eliminated a dependency. Sometimes the best engineering decision is removing something.

**No GPU in production.** ONNX Runtime runs inference on CPU fast enough for a single-user app, and the LLM is an API call. That keeps the whole stack on a single t3.medium at ~$33/month instead of a $300+/month GPU instance.

## Data

### Training Data

All ~177,000 training images come from iNaturalist research-grade observations — community-verified identifications, not scraped web images. A custom download script pulls observations sorted by community votes, targeting 1,500-2,500 images per species, with boosted counts for species the model struggled with in earlier runs.

The split script generates a stratified 70/15/15 train/val/test split. Four species pairs that are visually indistinguishable in photos (and equivalent for foraging purposes) are merged into single classes — highbush/lowbush blueberry, smooth/golden chanterelle, American elderberry/elderberry, white-pored/orange chicken of the woods — reducing 105 species to 101 training classes.

### Safety & Nutrition Data

Every piece of safety data is manually curated from published field guides and academic sources — Thayer's *The Forager's Harvest*, Peterson's *Field Guide to Edible Wild Plants*, USDA databases, and peer-reviewed papers. Source citations are embedded in every knowledge base entry. This was the most time-consuming part of the project, but for something that tells people what's safe to eat, "we asked an LLM" wasn't an option.

The safety dataset covers all 105 species with toxic lookalike warnings, protection status by state, edibility details, and preparation requirements. Nutrition data covers 95 species with macros, notable nutrients, and edible parts.

## Architecture
The request comes in with a photo and optional location. Geocoding resolves coordinates (GPS, city/state, or zip). The orchestrator is an async generator where each stage yields an SSE event as it completes, and `forage_stream.py` persists each result to the database before sending it to the client. Nutrition only runs on strong-confidence matches. If any stage fails, everything before it is already saved.

![alt text](forager_stream_flow.drawio.svg)


## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, async SQLAlchemy, Pydantic |
| Frontend | React 19, TypeScript, Vite, Tailwind, shadcn/ui, Zustand |
| Database | PostgreSQL |
| ML Inference | ONNX Runtime (EfficientNet-B7, 600px, 101 classes) |
| ML Training | PyTorch, timm, Mixup/CutMix, SWA, cosine annealing, label smoothing |
| Auth | JWT + httpOnly cookies, OAuth (Google, GitHub) |
| Weather | Open-Meteo API |
| Geocoding | OpenStreetMap Nominatim |
| Rate Limiting | slowapi + Redis |
| CI/CD | GitHub Actions (lint, test, build) |
| Python Tooling | uv, ruff, pytest |
| Infrastructure | Docker Compose, Terraform (AWS EC2, S3), Let's Encrypt |

## Project Structure

```
├── backend/           FastAPI API, agents, services, models
│   ├── app/
│   │   ├── agents/    Orchestrator + pipeline stages (safety, weather)
│   │   ├── api/       Route handlers, SSE streaming
│   │   ├── auth/      JWT + OAuth, middleware
│   │   ├── data/      Curated safety + nutrition JSON datasets
│   │   ├── db/        Async SQLAlchemy, Alembic migrations
│   │   ├── models/    ORM models (users, discoveries, locations)
│   │   └── services/  Classifier, geocoding, discovery CRUD
│   └── tests/
├── frontend/          React SPA: pages, components, stores
│   └── src/
│       ├── components/   UI components (results, journal, upload)
│       ├── pages/        Route-level page components
│       ├── stores/       Zustand state (auth, forage stream)
│       └── hooks/        Custom React hooks
├── ml/                Training pipeline + model export
│   ├── training/      Train scripts (B7, Lite4, Phase C)
│   ├── models/        Model architecture definitions
│   ├── scripts/       Data prep, ONNX export, splits
│   └── configs/       Training hyperparameters
└── infra/             Docker Compose, deploy scripts
```

## Frontend Architecture

The frontend isn't just a form that talks to an API, it's built around the streaming pipeline. A client-side async generator (`streamForage`) mirrors the backend pattern; it reads the SSE stream and yields typed events that the Zustand store consumes. The UI updates progressively as each event arrives; classification triggers navigation to the results page, then safety, nutrition, and weather panels fill in as they complete. No loading spinners or "please wait" screens.

State is split across two Zustand stores: `authStore` for session management and `forageStore` for the streaming identification lifecycle. The forage store tracks stream status, caches each event's data, and manages the transition from live streaming to persisted discovery.

The UI is mobile-first with a responsive bottom navigation bar on small screens and a top navbar on desktop. Component styling uses a design system of ~50 utility classes in a `@layer components` CSS file on top of Tailwind v4 and shadcn/ui primitives. 

## Testing & CI

The backend has integration tests that run against a real PostgreSQL instance, not mocked databases. Test coverage includes auth flows, safety agent verdicts, weather forecasting, ONNX transform regression, discovery CRUD, and location management.

CI runs on every push and PR via GitHub Actions:
- **Backend:** ruff lint -> Alembic migrations -> pytest (against a Postgres service container)
- **Frontend:** ESLint -> TypeScript build

Python dependencies are managed with uv, linting and formatting with ruff.

## ML Deep Dive

The model is an EfficientNet-B7 fine-tuned on ~177,000 iNaturalist research-grade images across 101 classes. A custom download script pulls observations sorted by community votes, with boosted counts for species the model struggled with in earlier runs. 600px input resolution — the extra detail matters when the difference between edible and toxic is a gill pattern or leaf serration.

### Training

Three phases, each with a specific purpose:

1. **Head-only** (5 epochs, lr=1e-3): Freeze the pretrained backbone, train only the new classifier layer. Protects ImageNet features from random gradients while the head learns to map to foraging species.
2. **Full fine-tune** (up to 50 epochs, lr=1e-4): Unfreeze everything at a lower learning rate. Cosine annealing schedule, early stopping at patience=8. Six regularization techniques running together: Mixup, CutMix, label smoothing, dropout, drop path, and RandAugment.
3. **Phase C refinement** (10 epochs, lr=1e-6): Loads the best checkpoint with a fresh optimizer, turns off Mixup/CutMix so the model trains on clean images with hard labels. Uses Stochastic Weight Averaging to find a flatter minimum. This phase sharpened decision boundaries that augmentation had slightly blurred.

The loss function switches depending on the training mode: `SoftTargetCrossEntropy` when Mixup/CutMix produces blended labels, standard `CrossEntropyLoss` with label smoothing for clean training. Validation always uses unsmoothed cross-entropy so metrics stay comparable across phases.

Final result: **95.7% validation accuracy**. The remaining errors are biologically meaningful, the model confuses species that humans confuse too (elderberry variants, black walnut vs butternut, chanterelle vs smooth chanterelle).

### CAM Heatmaps

The model exports as a dual-output ONNX file, logits and spatial feature maps from a single forward pass. In production, heatmaps are computed with numpy using the classifier's weight matrix, no PyTorch or gradient computation needed. The result shows exactly which part of the image drove the prediction.

### What's Next for the Model

The current model is strong on its 101 target species, but it doesn't know what it *doesn't* know, a dogwood bloom will confidently call it a wild strawberry because it's never seen dogwood. That's not acceptable for a foraging app.

The next training round adds out-of-distribution handling: common non-target species (dogwood, rhododendron, tulip poplar, etc.) trained as real classes so the model learns to positively identify them, plus a "not a plant" class for rocks, hands, and blurry shots. The UI would show "not a foraging target" instead of a wrong match. Energy scoring on raw logits adds a second layer of confidence gating on the backend. This is currently in development.

## What's Next

- **Out-of-distribution detection:** The model doesn't yet know what it doesn't know (see [What's Next for the Model](#whats-next-for-the-model) above). The next training round adds non-target species classes, a "not a plant" catch-all, and energy scoring as a backend confidence gate.
- **Offline/PWA mode:** A distilled EfficientNet-Lite4 (380px, ~12M params) trained from the B7's predictions, running inference directly in the browser via ONNX Web Runtime. Classification and static safety would work with no network connection, the architecture already separates these from the API-dependent stages.
- **LLM chat:** Conversational follow-ups about identified species ("can I eat the stems?", "what does it taste like?"), powered by RAG over the curated safety and nutrition knowledge base using pgvector embeddings. The schema and vector column already exist, this is mostly a frontend and prompt engineering effort. The backend already supports swappable LLM providers via config, Ollama for local development, API calls (Gemini, etc.) for production.

## License

All rights reserved. This code is shared for portfolio review and evaluation purposes only. You may not use, copy, modify, or distribute any part of this project without explicit written permission.

This project will transition to an open-source license once the roadmap items above are complete.

---

Built by [Lindsay Schwartz](https://linkedin.com/in/lindsayrschwartz)
