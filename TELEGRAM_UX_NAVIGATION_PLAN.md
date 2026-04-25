# Telegram UX Navigation Plan

## Purpose

Define a professional Telegram interaction model for the doctor that is:

- safe for healthcare workflows
- easy to navigate under real-world use
- resistant to duplicate clicks and stale callbacks
- clear during diet review and approval
- traceable when clinical content is edited

This document is the reference for future implementation work on Telegram UX.

## Current problems

1. Some inline button flows can feel fragile or confusing.
2. Old messages may still look actionable to the doctor.
3. The doctor needs clearer orientation about where she is in the flow.
4. The preview should support true clinical review before approval.
5. Editing meals in the 7-day plan must be visible, stable, and auditable.

## UX principles

1. Every clinically relevant action must be explicit.
2. Navigation must be predictable across all flows.
3. Drafts must remain editable until approval.
4. Approved diets must be treated as finalized clinical output.
5. The doctor should never be forced to guess the current step.
6. Old buttons must never be able to alter the active clinical state.

## Navigation model

Use a controlled wizard model for Telegram flows.

Each guided flow should support these universal actions:

- `Back`: return to the previous reversible step
- `Refresh current step`: rebuild the valid current screen
- `Cancel flow`: exit safely and return to menu

Each flow state should store:

- current step
- previous step stack
- patient context
- active message id for inline step
- whether the current step is reversible
- whether the current state is a draft review state

## Inline keyboard strategy

Telegram does not support true disabled buttons. The system should simulate it professionally.

Recommended behavior:

1. Replace active keyboards instead of simply removing them.
2. Show visual states such as:
   - `Selected: 14 days`
   - `Step completed`
   - `Already processed`
3. Keep navigation available:
   - `Back`
   - `Refresh current step`
   - `Cancel`
4. Reject stale callbacks in backend even if an old message is clicked.

## Standard flow structure for diet generation

### Phase A: Configuration

1. Select patient
2. Optional clinical note
3. Duration
4. Meals per day
5. Nutrition strategy
6. Style or macro preferences when applicable
7. Final pre-generation confirmation

### Phase B: Draft review

The generated plan should remain in `pending_approval`.

The doctor should be able to:

1. review summary data
2. review all 7 days
3. inspect individual meals
4. edit meals
5. regenerate with note
6. apply quick adjustments
7. discard
8. approve and export PDF

### Phase C: Approval

Approval should be a clear final action.

After approval:

- the draft is no longer directly editable
- PDF generation is based on the approved version
- future changes should generate a new draft version

## Preview redesign

The draft preview must become a real clinical review screen.

It should show:

1. patient name and key identifiers
2. calories, macros, duration, meals/day
3. clinical warnings or system alerts
4. recommendations
5. the full 7-day plan
6. each day split by meals
7. clear actions for:
   - `Edit meal`
   - `View day`
   - `Regenerate`
   - `Approve`
   - `Discard`

## 7-day review behavior

Recommended Telegram behavior:

1. The first preview message shows summary plus day navigation.
2. A `View full 7 days` action sends the diet in structured day blocks.
3. Each day can expose meal-level actions.
4. The doctor must be able to edit a meal without leaving the draft review context.

## Meal editing model

Meal editing should operate only on drafts.

Recommended workflow:

1. Doctor opens a specific day.
2. Doctor selects a meal slot.
3. Bot shows current meal text.
4. Doctor edits the content.
5. Backend updates only that draft meal.
6. Preview is regenerated or re-rendered with the new content.

Recommended model:

- free-text edit for speed
- backend keeps structural constraints
- audit the change

Minimum validations:

1. Preserve day and meal slot correctly.
2. Do not allow edits on approved diets.
3. Record manual changes distinctly from AI-generated content.
4. Warn if the edit obviously conflicts with allergies or restrictions.

## Reversibility rules

### Reversible steps

These should support `Back`:

- note selection
- duration
- meals per day
- nutrition strategy
- style selection
- macro preferences

### Non-final but editable states

These should support `Refresh current step`:

- draft preview
- quick adjustment menu
- meal edit selection

### Final actions

These should not be silently reversible:

- approve diet
- discard draft
- export approved PDF

If the doctor changes her mind after approval, the system should create a new draft version instead of mutating the approved artifact.

## Safety rules for healthcare context

1. Approved clinical output must be immutable in place.
2. Draft edits must be auditable.
3. Missing critical patient data should block generation when necessary.
4. Important warnings should remain visible before approval.
5. Navigation must never bypass clinical validation steps.

## Backend expectations

The Telegram backend should enforce:

1. stale callback rejection
2. one active valid inline message per wizard step
3. draft-only meal editing
4. row/state locking for critical transitions
5. version-safe approval and regeneration

## Proposed implementation phases

### Phase 1

Unify navigation and button state rules across Telegram flows.

Tasks:

1. standardize `Back`, `Refresh current step`, `Cancel`
2. formalize step stack in conversation state
3. make all inline steps validate active message id

### Phase 2

Redesign wizard UX for diet creation.

Tasks:

1. make all steps show current context
2. keep navigation visible after each choice
3. visually block processed buttons instead of simply dropping all controls

### Phase 3

Restore and strengthen clinical draft review.

Tasks:

1. show the 7-day plan clearly
2. preserve summary and warnings
3. support day and meal inspection from preview

### Phase 4

Recover stable meal editing on draft diets.

Tasks:

1. allow selection by day and meal slot
2. apply targeted meal edits
3. re-render draft preview after each edit
4. audit manual modifications

### Phase 5

Harden approval lifecycle.

Tasks:

1. keep approval as explicit final step
2. prevent editing approved diets directly
3. require new draft versions for post-approval changes

## Recommended final UX decision

For this project, the best professional solution is:

1. controlled Telegram wizard navigation
2. visually blocked action buttons with persistent navigation
3. full 7-day draft review before approval
4. meal-level editing on pending drafts
5. explicit approval boundary
6. auditability and version discipline appropriate for healthcare

## Deliverable outcome

When implemented, the doctor should be able to:

1. always know the current step
2. safely move back without losing control of the flow
3. review the full 7-day plan before approval
4. edit any meal in draft state
5. avoid accidental duplicate actions
6. trust that approved output is stable and traceable
