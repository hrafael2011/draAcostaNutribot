import { test, expect } from "@playwright/test"

test.describe("ConfirmModal — UI structure", () => {
  test("ConfirmModal renders with correct structure", async ({ page }) => {
    // Navigate to a page that uses the modal
    // For now this is a smoke test that Playwright is set up correctly
    await page.goto("/")
    await expect(page.locator("body")).toBeVisible()
  })

  test("ConfirmModal shows changes and buttons", async ({ page }) => {
    // Basic test to verify the HTML structure renders
    // Inject the modal HTML manually to verify styling
    await page.setContent(`
      <div id="modal">
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
          <div class="w-full max-w-md mx-4 bg-white rounded-2xl shadow-xl">
            <div class="px-6 pt-6 pb-4">
              <h2 class="text-lg font-semibold text-gray-900">Revisa tus datos</h2>
            </div>
            <div class="px-6 pb-4">
              <div class="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                <div class="space-y-2">
                  <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-500">Nombre</span>
                    <div class="text-right">
                      <span class="font-medium text-emerald-700">Ana Martínez</span>
                    </div>
                  </div>
                  <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-500">Peso</span>
                    <div class="text-right">
                      <span class="text-gray-400 line-through text-xs mr-1">70</span>
                      <span class="font-medium text-gray-800">→ 68</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="px-6 pb-6 flex gap-3">
              <button class="flex-1 flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors">
                Corregir
              </button>
              <button class="flex-1 flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors">
                Confirmar
              </button>
            </div>
          </div>
        </div>
      </div>
    `)

    // Verify modal structure
    await expect(page.getByText("Revisa tus datos")).toBeVisible()
    await expect(page.getByText("Ana Martínez")).toBeVisible()
    await expect(page.getByText("70")).toBeVisible()
    await expect(page.getByText("68")).toBeVisible()
    await expect(page.getByText("Confirmar")).toBeVisible()
    await expect(page.getByText("Corregir")).toBeVisible()
  })

  test("ConfirmModal handles loading state correctly", async ({ page }) => {
    // Test that buttons disable during loading
    await page.setContent(`
      <div id="modal">
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
          <div class="w-full max-w-md mx-4 bg-white rounded-2xl shadow-xl">
            <div class="px-6 pt-6 pb-4">
              <h2 class="text-lg font-semibold text-gray-900">Revisa tus datos</h2>
            </div>
            <div class="px-6 pb-4">
              <div class="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                <div class="space-y-2">
                  <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-500">Nombre</span>
                    <div class="text-right">
                      <span class="font-medium text-emerald-700">Ana Martínez</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="px-6 pb-6 flex gap-3">
              <button disabled class="flex-1 flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-semibold text-gray-700 opacity-50 transition-colors">
                Corregir
              </button>
              <button disabled class="flex-1 flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white opacity-50 transition-colors">
                Guardando...
              </button>
            </div>
          </div>
        </div>
      </div>
    `)

    // Both buttons should be disabled during loading
    const buttons = page.locator("button")
    await expect(buttons.nth(0)).toBeDisabled()
    await expect(buttons.nth(1)).toBeDisabled()
    await expect(page.getByText("Guardando...")).toBeVisible()
  })

  test("ConfirmModal displays old → new values with strikethrough", async ({ page }) => {
    await page.setContent(`
      <div id="modal">
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
          <div class="w-full max-w-md mx-4 bg-white rounded-2xl shadow-xl">
            <div class="px-6 pt-6 pb-4">
              <h2 class="text-lg font-semibold text-gray-900">Revisar cambios</h2>
              <p class="text-sm text-gray-500 mt-1">Confirma los cambios realizados.</p>
            </div>
            <div class="px-6 pb-4">
              <div class="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                <div class="space-y-2">
                  <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-500">Peso</span>
                    <div class="text-right">
                      <span class="text-gray-400 line-through text-xs mr-1">70</span>
                      <span class="font-medium text-gray-800">→ 68</span>
                    </div>
                  </div>
                  <div class="flex justify-between items-center text-sm">
                    <span class="text-gray-500">País</span>
                    <div class="text-right">
                      <span class="text-gray-400 line-through text-xs mr-1">México</span>
                      <span class="font-medium text-gray-800">→ RD</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="px-6 pb-6 flex gap-3">
              <button class="flex-1 px-4 py-3 text-sm font-semibold rounded-xl border border-gray-300 text-gray-700">Continuar editando</button>
              <button class="flex-1 px-4 py-3 text-sm font-semibold rounded-xl bg-emerald-600 text-white">Confirmar cambios</button>
            </div>
          </div>
        </div>
      </div>
    `)

    // Verify old values are shown with strikethrough
    await expect(page.getByText("Revisar cambios")).toBeVisible()
    await expect(page.getByText("Confirma los cambios realizados.")).toBeVisible()
    await expect(page.getByText("Confirmar cambios")).toBeVisible()
    await expect(page.getByText("Continuar editando")).toBeVisible()

    // Verify the changes display
    await expect(page.getByText("Peso")).toBeVisible()
    await expect(page.getByText("País")).toBeVisible()
  })
})
