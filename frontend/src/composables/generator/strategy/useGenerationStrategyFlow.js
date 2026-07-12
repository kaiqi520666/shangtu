import { computed, ref } from "vue";

function normalizeSnapshotValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeSnapshotValue(item));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, normalizeSnapshotValue(value[key])]),
    );
  }
  return value ?? null;
}

function stringifySnapshot(value) {
  return JSON.stringify(normalizeSnapshotValue(value));
}

export function createStrategySnapshot(value) {
  return normalizeSnapshotValue(value);
}

export function useGenerationStrategyFlow({
  buildInputSnapshot,
  onItemsChange,
  initialStep = "config",
} = {}) {
  const workflowStep = ref(initialStep);
  const strategyBrief = ref("");
  const strategyItems = ref([]);
  const strategySnapshot = ref(null);

  const strategyLoading = computed(() => workflowStep.value === "strategy-loading");
  const strategyPanelVisible = computed(
    () => workflowStep.value === "strategy-loading" || workflowStep.value === "strategy-review",
  );
  const hasStrategy = computed(() => strategyItems.value.length > 0);
  const currentInputSnapshot = computed(() =>
    buildInputSnapshot ? createStrategySnapshot(buildInputSnapshot()) : null,
  );
  const strategyDirty = computed(() => {
    if (!hasStrategy.value || !strategySnapshot.value) return false;
    return stringifySnapshot(currentInputSnapshot.value) !== stringifySnapshot(strategySnapshot.value);
  });
  const canGenerateWithStrategy = computed(
    () => hasStrategy.value && !strategyLoading.value && !strategyDirty.value,
  );

  function setStrategyItems(items, { notify = true } = {}) {
    strategyItems.value = Array.isArray(items) ? [...items] : [];
    if (notify) {
      onItemsChange?.(strategyItems.value);
    }
  }

  function startStrategyLoading({ snapshot = null, clear = true } = {}) {
    workflowStep.value = "strategy-loading";
    strategySnapshot.value = snapshot ? createStrategySnapshot(snapshot) : null;
    if (clear) {
      strategyBrief.value = "";
      setStrategyItems([], { notify: false });
    }
  }

  function setStrategyResult({ brief = "", items = [], snapshot = null, step = "strategy-review" } = {}) {
    strategyBrief.value = brief;
    strategySnapshot.value = createStrategySnapshot(snapshot || currentInputSnapshot.value);
    setStrategyItems(items);
    workflowStep.value = step;
  }

  function resetStrategy(step = "config") {
    strategyBrief.value = "";
    strategySnapshot.value = null;
    setStrategyItems([], { notify: false });
    workflowStep.value = step;
  }

  function setStrategyStep(step) {
    workflowStep.value = step;
  }

  async function runStrategy({
    snapshot = null,
    request,
    normalizeResult,
    emptyMessage,
    failureMessage,
  }) {
    startStrategyLoading({ snapshot });
    try {
      const response = await request();
      if (response.code !== 0) {
        setStrategyStep("config");
        return { ok: false, message: response.message || failureMessage };
      }
      const result = normalizeResult(response.data || {});
      if (!Array.isArray(result.items) || result.items.length === 0) {
        setStrategyStep("config");
        return { ok: false, message: emptyMessage };
      }
      setStrategyResult({ ...result, snapshot });
      return { ok: true, ...result };
    } catch (error) {
      setStrategyStep("config");
      return { ok: false, message: failureMessage, error };
    }
  }

  function updateStrategyItem(index, patch) {
    const current = strategyItems.value[index];
    if (!current) return;
    const nextItems = [...strategyItems.value];
    nextItems[index] = {
      ...current,
      ...patch,
    };
    setStrategyItems(nextItems);
  }

  function reorderStrategyItems(nextItems) {
    setStrategyItems(nextItems);
  }

  function removeStrategyItem(index) {
    setStrategyItems(strategyItems.value.filter((_, currentIndex) => currentIndex !== index));
  }

  function backToConfig() {
    setStrategyStep("config");
  }

  return {
    workflowStep,
    strategyBrief,
    strategyItems,
    strategySnapshot,
    currentInputSnapshot,
    strategyDirty,
    strategyLoading,
    strategyPanelVisible,
    hasStrategy,
    canGenerateWithStrategy,
    startStrategyLoading,
    setStrategyResult,
    resetStrategy,
    setStrategyStep,
    runStrategy,
    updateStrategyItem,
    reorderStrategyItems,
    removeStrategyItem,
    backToConfig,
  };
}
