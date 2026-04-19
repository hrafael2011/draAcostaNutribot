# Telegram manual smoke checklist

## Goal

Short live validation for the real Telegram channel after unit and simulated E2E are green.

## Preconditions

- Compose stack up with `db`, `backend`, and `web`.
- Public webhook available if live Telegram delivery is being validated.
- Doctor account linked to the bot.
- At least one patient with complete enough profile to generate a plan.

## Checklist

1. Open the bot and confirm the doctor binding / main menu works.
2. Open a patient from Telegram and verify the patient action menu renders.
3. Start diet generation from guided menu.
4. Complete note, duration, `meals_per_day`, and strategy mode.
5. Confirm the preview appears and the meal structure shown matches the selected count.
6. Approve and verify PDF delivery.
7. Start diet generation from natural language, then complete the remaining wizard steps.
8. Trigger a quick adjustment from preview and verify the refreshed preview is coherent.
9. Trigger regeneration from preview, change duration and meals/day, and verify the refreshed preview updates.
10. Try one invalid duration and one invalid meals/day input and confirm the bot answers safely.

## Execution status for this audit

- Prepared: yes
- Public webhook reachable: yes
- Webhook synced in Telegram: yes
- Executed live against real Telegram webhook: no
- Reason: this audit was completed in an automated local session without a human Telegram interaction loop, so the end-to-end doctor interaction inside Telegram still needs a person on the device.

## Suggested live command sequence

```text
docker compose up -d db backend web
# optional public tunnel, if this environment should receive live Telegram updates
docker compose up -d ngrok
```
