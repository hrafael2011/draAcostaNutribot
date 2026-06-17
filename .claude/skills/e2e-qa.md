---
name: e2e
description: Run Playwright e2e tests for the diet agent app
---

Run Playwright e2e tests. First ensure PostgreSQL and backend are running:

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent
./start.sh --backend
```

Then in another terminal run the tests:

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend

# List all available tests
npx playwright test --list

# Run all tests (headless)
npx playwright test

# Run with visible browser
npx playwright test --headed

# Run a single test file
npx playwright test e2e/confirm-modal.spec.ts

# Run with visible browser + slow motion (for debugging)
npx playwright test --headed --slow-mo 500
```

Test files: `frontend/e2e/*.spec.ts`
