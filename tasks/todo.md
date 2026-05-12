# TODO

## F05 — Mobile skeleton (next)

Steps:
1. `cd apps/mobile` and write Expo TS scaffold manually (avoid `create-expo-app` prompts)
2. Add deps: expo, react, react-native, expo-router (for file-based routing matching web), typescript, jest, @testing-library/react-native, jest-expo
3. Layout: `app/_layout.tsx`, `app/index.tsx`, basic Expo Router setup
4. **Write failing test first** — `app/__tests__/index.test.tsx` asserts the home screen renders heading
5. Implement minimal `app/index.tsx`
6. Configure jest with `jest-expo` preset
7. Add `package.json` scripts: `start`, `android`, `ios`, `web`, `lint`, `typecheck`, `test`

## Up next

- F06 — Shared packages
- F07 — Device model + register

## Blocked

_(none)_
