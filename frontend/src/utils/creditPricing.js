export function applyConsumptionMultiplier(baseCost, multiplier = 1) {
  return Math.ceil(Number(baseCost || 0) * Number(multiplier || 1));
}

export function multiplyCreditCosts(costs, multiplier = 1, round = false) {
  return Object.fromEntries(
    Object.entries(costs || {}).map(([key, value]) => {
      const adjusted = Number(value) * Number(multiplier || 1);
      return [key, round ? Math.ceil(adjusted) : adjusted];
    }),
  );
}
