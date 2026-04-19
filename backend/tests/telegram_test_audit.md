# Telegram test audit

## Coverage matrix

| Area | Scenario | Coverage | Notes |
| --- | --- | --- | --- |
| Natural language | Safe intents (`patients`, `thanks`, stats) | Covered | `test_telegram_free_text_safe_intent_patients`, `test_telegram_thanks_is_safe_reply`, `test_telegram_nl_diet_stats_and_lb_weight_confirm` |
| Natural language | Start diet flow from free text | Covered | `test_telegram_natural_language_starts_guided_diet` |
| Natural language | Full flow to preview/approval | Covered | `test_telegram_natural_language_manual_flow_reaches_preview_and_approval` |
| Guided menu | Cancel after note step | Covered | `test_telegram_guided_diet_flow_and_cancel` |
| Guided menu | Duration -> meals/day -> strategy -> confirm -> preview | Covered | `test_telegram_diet_quick_adjust_regenerates_preview`, `test_telegram_regenerate_with_duration_callback` |
| Guided menu | Meals/day by callback and by text | Covered | `test_meals_callback_moves_to_strategy_mode`, `test_stateful_meals_per_day_accepts_numeric_text` |
| Guided menu | Invalid meals/day text | Covered | `test_stateful_meals_per_day_rejects_invalid_text`, `test_telegram_guided_flow_rejects_invalid_duration_meals_and_stale_confirm` |
| Guided menu | Manual targets flow | Covered | `test_smd_manual_triggers_manual_kcal_step`, `test_manual_stateful_flow_reaches_confirm_with_values`, `test_telegram_natural_language_manual_flow_reaches_preview_and_approval` |
| Preview | Dynamic meal structures 2/3/4/5 | Covered | `test_format_diet_preview_shows_expected_meal_structure` |
| Preview | Approve, PDF, history PDF | Covered | `test_telegram_history_with_pdf_button`, `test_diet_pdf_export`, NL/manual approval flow |
| Resume | Missing height -> metric capture -> resume | Covered | `test_telegram_resume_diet_after_missing_height` |
| Quick adjust | Regenerates preview | Covered | `test_telegram_diet_quick_adjust_regenerates_preview` |
| Stale/fragile state | Old confirm callback before wizard completion | Covered | `test_telegram_guided_flow_rejects_invalid_duration_meals_and_stale_confirm` |
| Stale/fragile state | Wrong awaiting for duration callbacks | Covered | `test_pickdur_rejects_wrong_awaiting`, `test_pickdur_rejects_patient_id_mismatch`, `test_pickrdur_rejects_diet_id_mismatch` |

## Test execution

Validated suite:

```text
backend/tests/test_telegram_stateful_text.py
backend/tests/test_telegram_strategy_callbacks.py
backend/tests/test_telegram_diet_messages.py
backend/tests/test_e2e_flow.py
```

Result:

```text
33 passed in 141.78s
```

Operational note:

- For local E2E, the test process must inherit the backend environment and point `DATABASE_URL` to a reachable Postgres from the compose stack.
- Real-channel preflight validated during the audit: `web` was started, the ngrok endpoint answered `200` on `/api/telegram/webhook`, and `./scripts/sync-telegram-webhook.sh` registered the public webhook successfully.

## Bug log

### Closed during audit

1. `High` - stale `diet:confirm:*` callback could bypass wizard steps
   - Flow: guided menu / stale callback
   - Actual result: confirm callback executed even when the wizard had not reached `diet_confirm`, so new required steps like `meals_per_day` and strategy mode could be skipped with an old button.
   - Expected result: reject the callback with a safe message when the state is not `diet_confirm` for that patient.
   - Type: bug
   - Status: fixed in `backend/app/services/telegram_handler.py` and covered by `test_telegram_guided_flow_rejects_invalid_duration_meals_and_stale_confirm`.

### Open items / residual risk

1. `Media` - quick adjustments remain generic for all meal structures
   - Flow: preview -> quick adjustments
   - Actual result: the quick menu always exposes `snack_add` and `snack_rm`, even when the active plan uses `2` or `5` meals and the clinical structure is more nuanced.
   - Expected result: quick adjustments should either adapt to the current `meal_slots` or explain when an adjustment would reshape the structure.
   - Type: UX / product gap

2. `Media` - Telegram E2E depends on external local setup
   - Flow: test execution
   - Actual result: if the backend env is not exported or the test process points to the wrong database, webhook/binding tests fail with configuration or auth errors unrelated to business logic.
   - Expected result: a single documented command or fixture should bootstrap a deterministic local E2E environment.
   - Type: test infrastructure gap

3. `Baja` - test environment warns about short JWT key
   - Flow: local pytest execution
   - Actual result: `InsecureKeyLengthWarning` appears during E2E.
   - Expected result: test/local env uses a sufficiently long key to keep signal clean.
   - Type: operational hygiene
