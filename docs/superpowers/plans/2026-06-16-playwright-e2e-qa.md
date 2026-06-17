# Playwright E2E + Custom QA Skill

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Agregar tests e2e con Playwright y crear un skill invocable con `/e2e` para correrlos.

**Architecture:** Playwright con navegador Chromium headless. Tests en `frontend/e2e/`. Skill personalizado en `.claude/skills/e2e-qa.md`.

**Tech Stack:** Playwright, TypeScript, React

---

### Task 1: Instalar y configurar Playwright

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/e2e/tsconfig.json`
- Create: `frontend/e2e/confirm-modal.spec.ts`

- [ ] **Step 1: Instalar Playwright**

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npm install -D @playwright/test && npx playwright install chromium 2>&1 | tail -5
```

Verificar:
```bash
npx playwright --version
```

- [ ] **Step 2: Crear config de Playwright**

Crear `frontend/playwright.config.ts`:
```ts
import { defineConfig } from "@playwright/test"

export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
  },
  webServer: [
    {
      command: "cd ../backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8002",
      port: 8002,
      timeout: 15000,
      reuseExistingServer: true,
    },
    {
      command: "npm run dev",
      port: 5173,
      timeout: 15000,
      reuseExistingServer: true,
    },
  ],
})
```

- [ ] **Step 3: Verificar que corre**

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npx playwright test --list 2>&1 | head -10
```

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/playwright.config.ts
git commit -m "test: install and configure Playwright"
```

---

### Task 2: Escribir tests e2e del modal de confirmación

**Files:**
- Create: `frontend/e2e/confirm-modal.spec.ts`

- [ ] **Step 1: Crear el test file**

```ts
import { test, expect } from "@playwright/test"

// ── Helper: navega a un intake de registro con token válido ──
async function setupRegisterPage(page: any) {
  // NOTA: Este test necesita un token de intake válido en la DB.
  // Para tests locales, se puede crear un token manualmente.
  // En CI, se necesita un setup que siembre datos.
  await page.goto("/intake/demo-register-token")
  await expect(page.getByText("Registro de Paciente")).toBeVisible()
}

test.describe("ConfirmModal — paciente registro", () => {
  test("muestra resumen antes de confirmar", async ({ page }) => {
    await setupRegisterPage(page)

    // Llenar campos
    await page.fill("input[name=first_name]", "Ana")
    await page.fill("input[name=last_name]", "Martínez")
    // ... llenar resto de campos según el formulario real

    // Click en enviar → debe aparecer el modal
    await page.click("button:has-text('Enviar registro')")
    await expect(page.getByText("Revisa tus datos")).toBeVisible()

    // Verificar que muestra los datos ingresados
    await expect(page.getByText("Ana Martínez")).toBeVisible()
    await expect(page.getByText("Confirmar y enviar")).toBeVisible()
    await expect(page.getByText("Corregir")).toBeVisible()
  })

  test('"Corregir" cierra el modal sin enviar', async ({ page }) => {
    await setupRegisterPage(page)
    await page.fill("input[name=first_name]", "Ana")
    await page.click("button:has-text('Enviar registro')")
    await expect(page.getByText("Revisa tus datos")).toBeVisible()
    await page.click("button:has-text('Corregir')")
    await expect(page.getByText("Revisa tus datos")).not.toBeVisible()
    // El formulario sigue visible con los datos intactos
    await expect(page.inputValue("input[name=first_name]")).resolves.toBe("Ana")
  })
})

test.describe("ConfirmModal — doctor edita perfil", () => {
  test("muestra cambios antes de guardar", async ({ page }) => {
    // Login como doctor
    await page.goto("/login")
    await page.fill("input[name=email]", "demo@doctor.com")
    await page.fill("input[name=password]", "demo123")
    await page.click("button:has-text('Iniciar sesión')")

    // Navegar a un paciente existente
    await page.goto("/patients/1")
    await expect(page.getByText("Perfil Clínico")).toBeVisible()

    // Modificar un campo
    await page.fill("input[name=weight_kg]", "72")
    await page.click("button:has-text('Guardar')")

    // Verificar modal
    await expect(page.getByText("Revisar cambios")).toBeVisible()
    await expect(page.getByText("Peso")).toBeVisible()
    await expect(page.getByText("Confirmar cambios")).toBeVisible()
    await expect(page.getByText("Continuar editando")).toBeVisible()
  })

  test('"Continuar editando" vuelve al formulario', async ({ page }) => {
    await page.goto("/login")
    await page.fill("input[name=email]", "demo@doctor.com")
    await page.fill("input[name=password]", "demo123")
    await page.click("button:has-text('Iniciar sesión')")
    await page.goto("/patients/1")
    await page.fill("input[name=weight_kg]", "75")
    await page.click("button:has-text('Guardar')")
    await expect(page.getByText("Revisar cambios")).toBeVisible()
    await page.click("button:has-text('Continuar editando')")
    await expect(page.getByText("Revisar cambios")).not.toBeVisible()
  })
})
```

NOTA: Estos tests asumen datos de demo existentes. Ajustar según el estado real de la DB local.

- [ ] **Step 2: Verificar que los tests se compilan**

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npx playwright test --list 2>&1 | head -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/confirm-modal.spec.ts
git commit -m "test: add e2e tests for confirmation modals"
```

---

### Task 3: Crear skill `/e2e` invocable

**Files:**
- Create: `.claude/skills/e2e-qa.md`

- [ ] **Step 1: Crear directorio y skill**

```bash
mkdir -p /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/.claude/skills
```

Crear `.claude/skills/e2e-qa.md`:
```markdown
---
name: e2e
description: Run Playwright e2e tests for the diet agent app
---

Run e2e tests with Playwright.

1. Start PostgreSQL:
   ```bash
   cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent && docker compose up -d db
   ```

2. Ensure backend virtual env exists:
   ```bash
   cd backend && source .venv/bin/activate
   ```

3. Run the tests:
   ```bash
   cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npx playwright test --headed
   ```

   For headless mode (no browser window):
   ```bash
   cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npx playwright test
   ```

   Run a single test file:
   ```bash
   npx playwright test e2e/confirm-modal.spec.ts
   ```

   Run with visible browser and slow motion:
   ```bash
   npx playwright test --headed --slow-mo 500
   ```
```

- [ ] **Step 2: Verificar que el skill se ve bien**

```bash
cat /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/.claude/skills/e2e-qa.md | head -10
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/e2e-qa.md
git commit -m "feat: add /e2e skill for running Playwright tests"
```

---

### Task 4: Verificación general

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npx playwright test --list
```
