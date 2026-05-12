# TODO

## F04 — Web skeleton (next)

Steps:
1. `cd apps/web` and scaffold Next.js App Router + TS manually (avoid `create-next-app` interactive prompts)
2. Add deps: next, react, react-dom, typescript, vitest, @vitejs/plugin-react, jsdom, @testing-library/react
3. Layout: `app/layout.tsx`, `app/page.tsx`, basic `app/health/page.tsx` or component test
4. tsconfig + next-env.d.ts + eslint config
5. **Write failing test first** — `app/__tests__/home.test.tsx` asserts the home page renders with a heading
6. Implement minimal `app/page.tsx` to pass
7. Add `package.json` scripts: `dev`, `build`, `start`, `lint`, `typecheck`, `test`

## Up next

- F05 — Mobile skeleton
- F06 — Shared packages

## Blocked

_(none)_
