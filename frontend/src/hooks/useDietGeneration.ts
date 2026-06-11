import { useMutation } from "@tanstack/react-query"
import {
  generateDiet,
  regenerateDiet,
  approveDiet,
  discardDiet,
  quickAdjustDiet,
  updateDietMeals,
} from "../services/api"

export function useDietGeneration() {
  const generate = useMutation({
    mutationFn: (body: Parameters<typeof generateDiet>[0]) => generateDiet({ ...body }),
  })

  const regenerate = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof regenerateDiet>[1] }) =>
      regenerateDiet(id, body),
  })

  const approve = useMutation({
    mutationFn: (dietId: number) => approveDiet(dietId),
  })

  const discard = useMutation({
    mutationFn: (dietId: number) => discardDiet(dietId),
  })

  const quickAdjust = useMutation({
    mutationFn: ({ dietId, adjustment }: { dietId: number; adjustment: string }) =>
      quickAdjustDiet(dietId, adjustment),
  })

  const editMeals = useMutation({
    mutationFn: ({
      dietId,
      meals,
    }: {
      dietId: number
      meals: { day_index: number; slot_key: string; meal_text: string }[]
    }) => updateDietMeals(dietId, { meals }),
  })

  return { generate, regenerate, approve, discard, quickAdjust, editMeals }
}
