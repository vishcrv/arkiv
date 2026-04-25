# Arkiv — stage 02 · Frontend

Second stage of Arkiv: a React single-page app built to replace the terminal UI. No backend yet — pages render off hardcoded empty arrays with `TODO` markers where the real data will later plug in.

Stack:

- **React 19** + React Router
- **Vite** dev server on `:5173` with HMR
- **Tailwind v4** + Base UI component primitives
- Design system: "Quiet Library" — warm linen light mode, deep walnut dark mode, oklch colors

## Architecture

[`docs/diagrams/architecture.html`](docs/diagrams/architecture.html)

Browser loads the SPA from Vite. Pages are wired up but the data calls are still stubs — this branch represents the moment React stood on its own, before the Salesforce backend came online in the next stage.

> Note: this branch continued to evolve past the "no backend" snapshot shown here — the HEAD of `frontend` already has the FastAPI + Salesforce wiring from the next stage mixed in. The diagram captures the stage *as intended*, not the branch tip verbatim.

## Running it

```bash
cd frontend
npm install
npm run dev
```

## Next stages

See the `saleforce` branch for the first real backend, and `main` for the current MySQL-backed stack. The `cli` branch holds the pre-frontend terminal version.
