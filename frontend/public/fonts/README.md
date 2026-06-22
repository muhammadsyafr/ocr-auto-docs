# Self-hosted fonts (Coral Stay)

Place these woff2 files here to activate the design typography offline (no Google CDN):

- `NunitoSans-Bold.woff2` (weights 700, 800 — display)
- `DMSans-Regular.woff2` (weights 400–600 — body)
- `JetBrainsMono-Regular.woff2` (weight 400 — code/JSON)

Download once from the font sources and commit them. Until present, the UI
falls back to `system-ui` (see `tailwind.config.ts`).
