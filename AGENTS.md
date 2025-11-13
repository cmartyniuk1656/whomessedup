# AGENTS Playbook

Welcome! This file documents the shared mindset we follow when touching this repo. Read it before you ship anything.

## Guiding Principles

- **Modularity first.** When you add logic, ask “should this live in a dedicated module/hook/component?” Shared helpers belong under `who_messed_up/services/` (backend) or `frontend/src/{components,hooks,config,utils}` (frontend). `who_messed_up/service.py` is only a re-export layer.
- **Reusability.** New features should prefer composing existing building blocks. If you find yourself copying logic, pause and look for an existing helper to wrap, or factor a new one out so future work can reuse it.
- **Readability over cleverness.** Choose explicit names, avoid hidden side effects, and keep components/hooks small. Document non-obvious decisions with short comments.
- **Incremental evolution.** Make small, verifiable steps. After each refactor, run the relevant regression snapshots (`scripts/capture_regressions.py`) or `npm run build` on the frontend to ensure behavior is unchanged.

## Backend Workflow

- Shared logic lives in `who_messed_up/services/…`. When creating a new capability (e.g., a report calculator, data fetcher), add a module there and re-export via `who_messed_up/service.py`.
- Always consider whether the logic already exists in another service module before writing new code. Extend the existing module if appropriate.
- After touching backend services, run the targeted regression cases (ghosts, phase-damage, add damage) to ensure golden snapshots still match.

## Frontend Workflow

- Configuration data (tile definitions, class colors, etc.) lives under `frontend/src/config`. 
- Cross-cutting logic lives in hooks (`frontend/src/hooks`). For example, `useTileRunner` handles fetch + polling, `useCsvExporter` handles CSV creation.
- UI should be composed of small components in `frontend/src/components` with presentational concerns only. Keep `App.jsx` as thin orchestration glue.
- Utilities (formatters, shared helpers) belong under `frontend/src/utils`.
- When you add a feature, check first if there’s a component/hook you can reuse. If not, consider whether the new abstraction could help future tiles or reports.
- Run `npm run build` (or `npm run lint/test` if applicable) after changes to ensure the UI compiles.

## Pull Request / Change Discipline

- Keep changes scoped. Refactor first, add features second—don’t mix large refactors with new behavior unless unavoidable.
- Whenever you extract logic, ensure any old entry points re-export or delegate so the public API stays stable unless intentionally changed.
- Respect existing formatting (Prettier/ESLint defaults, 2-space indentation) to keep diffs focused.

## Testing & Verification

- Backend: run the regression snapshots relevant to the code you touched. (e.g., `ghosts_*`, `nexus_phase_*`, `dimensius_*`). Add new snapshot cases if you add new report types.
- Frontend: at minimum run `npm run build`. If you add UI that’s easy to test, add simple RTL tests or Storybook entries.
- When bugs are found, add regression coverage (snapshot, unit test, or Storybook notes) so we don’t repeat them.

## Communication

- Leave breadcrumbs. When you make structural changes, update this file or README sections so future agents understand the rationale.
- If you introduce new abstractions, document their intended use at the top of the module/component file.

Thanks for keeping the codebase healthy for the next agent! 
