import { computed, onBeforeUnmount, reactive, ref } from "vue";
import { getAssetDownloadUrl } from "@/api/assets.js";
import { createVoiceoverTask, deleteVoiceoverTask, getVoiceoverConfig, getVoiceoverTask } from "@/api/voiceover.js";
import { useMediaBatchRunner } from "@/composables/generator/batch/useMediaBatchRunner.js";
import { createBatchFinishedHandler, useGenerationCards } from "@/composables/generator/useGenerationCards.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";
import { useAuthStore } from "@/stores/auth.js";
import { applyConsumptionMultiplier } from "@/utils/creditPricing.js";

const POLL_INTERVAL_MS = 5000;

export function countVoiceoverCharacters(text) { return String(text || "").replace(/\s/g, "").length; }

export function useVoiceoverGenerator({ onJobCreated } = {}) {
  const toast = useToast();
  const confirm = useConfirm();
  const authStore = useAuthStore();
  const config = reactive({ textLimit: 5000, creditCostPer100Chars: 1, consumptionMultiplier: 1, format: "mp3", sampleRate: 24000 });
  const settings = reactive({ text: "", voice: null, rate: 1, pitch: 1, volume: 100, instruction: "" });

  async function pollTask(taskId) {
    const result = await getVoiceoverTask(taskId);
    if (result.code === 0 && Number.isFinite(Number(result.data?.credits))) authStore.updateCredits(result.data.credits);
    return result;
  }

  const cards = useGenerationCards({
    getTask: pollTask,
    pollIntervalMs: POLL_INTERVAL_MS,
    mediaLabel: "音频",
    preloadResult: false,
    getLogPrefix: (card) => card.strategyTitle || "AI配音",
    onBatchFinished: createBatchFinishedHandler({
      genLogs: null,
      toast,
      doneLog: "AI配音任务已结束",
      successText: "AI配音生成完成",
      allFailedText: "AI配音生成失败，请稍后重试",
      partialFailedText: () => "部分配音生成失败",
    }),
  });

  const runner = useMediaBatchRunner({
    scenario: "voiceover",
    cards,
    toast,
    onJobCreated,
    mediaUnit: "条",
    resetSceneState() { Object.assign(settings, { text: "", voice: null, rate: 1, pitch: 1, volume: 100, instruction: "" }); },
    applyJobData(data) {
      const snapshot = data.settings || {};
      settings.text = data.input_text || "";
      settings.rate = Number(snapshot.rate ?? 1);
      settings.pitch = Number(snapshot.pitch ?? 1);
      settings.volume = Number(snapshot.volume ?? 100);
      settings.instruction = snapshot.instruction || "";
      settings.voice = snapshot.voice_id ? { voice_id: snapshot.voice_id, name: snapshot.voice_name, trait: snapshot.voice_trait, category: snapshot.voice_category, supports_instruct: Boolean(snapshot.supports_instruct) } : null;
    },
    restoreCard(item) {
      const card = cards.restoreCard(item, { strategyTitle: item.title || "AI配音", settingsSnapshot: item.settings_snapshot || null });
      card.assetId = item.asset_id || "";
      return card;
    },
  });

  const actions = useCardActions({
    outputCards: cards.outputCards,
    currentTaskTitle: runner.currentTaskTitle,
    getCardName: (card) => card.strategyTitle || "AI配音",
    getDownloadUrl: (card) => getAssetDownloadUrl("audio", card.assetId),
    mediaLabel: "音频",
    mediaUnit: "条",
    archiveName: "AI配音",
    toast,
  });

  const canGenerate = computed(() => Boolean(settings.voice?.voice_id) && countVoiceoverCharacters(settings.text) > 0 && countVoiceoverCharacters(settings.text) <= config.textLimit && !cards.creatingBatch.value && !cards.generating.value);

  async function loadConfig() {
    try {
      const result = await getVoiceoverConfig();
      if (result.code !== 0) return toast.error(result.message || "配音配置加载失败");
      config.textLimit = Number(result.data?.text_limit || 5000);
      config.creditCostPer100Chars = Number(result.data?.credit_cost_per_100_chars || 1);
      config.consumptionMultiplier = Number(result.data?.consumption_multiplier || 1);
      config.format = result.data?.format || "mp3";
      config.sampleRate = Number(result.data?.sample_rate || 24000);
    } catch { toast.error("配音配置加载失败"); }
  }

  function updateSettings(next) {
    Object.assign(settings, next);
    if (next.voice && !next.voice.supports_instruct) settings.instruction = "";
  }

  async function generate() {
    if (!canGenerate.value) return toast.info("请选择音色并输入有效配音文本");
    const voice = settings.voice;
    const snapshot = { model: "cosyvoice-v3-flash", voice_id: voice.voice_id, voice_name: voice.name, voice_trait: voice.trait || "", voice_category: voice.category || "", supports_instruct: Boolean(voice.supports_instruct), rate: settings.rate, pitch: settings.pitch, volume: settings.volume, instruction: settings.instruction, format: config.format, sample_rate: config.sampleRate, character_count: countVoiceoverCharacters(settings.text) };
    await runner.enqueueMediaBatch({
      queue: [{ id: "voiceover", title: voice.name || "AI配音" }],
      snapshotPayload: { settings: snapshot, input_text: settings.text },
      initialLogs: ["AI配音任务初始化..."],
      repeatLog: "开始生成新的配音",
      buildSettingsSnapshot: () => ({ ...snapshot }),
      createCard({ item, sortOrder, batchRunId, settingsSnapshot }) {
        const card = cards.createCard({ typeId: "voiceover", strategyTitle: item.title, strategyContent: settings.text, sortOrder, batchRunId, settingsSnapshot });
        card.creditCost = applyConsumptionMultiplier(Math.ceil(countVoiceoverCharacters(settings.text) / 100) * config.creditCostPer100Chars, config.consumptionMultiplier);
        return card;
      },
      async createTask({ jobId }) {
        const result = await createVoiceoverTask({ job_id: jobId, text: settings.text, voice_id: voice.voice_id, rate: settings.rate, pitch: settings.pitch, volume: settings.volume, instruction: voice.supports_instruct ? settings.instruction : null });
        if (result.code === 0 && Number.isFinite(Number(result.data?.credits))) authStore.updateCredits(result.data.credits);
        return result;
      },
      getCreateLog: () => `正在生成 [${voice.name}]...`,
      getFailLogName: () => voice.name,
      allFailedMessage: "AI配音任务创建失败",
      saveErrorMessage: "保存AI配音配置失败",
      taskIdMissingMessage: "AI配音任务创建失败：后端未返回任务 ID",
      insertCards: "after-success",
      preferCreateErrorAsToast: true,
    });
  }

  async function removeCard(card) {
    if (!card?.taskId) return;
    const ok = await confirm.open({ title: "删除音频", message: "确定删除这条音频吗？该音频也会从资产库移除。", confirmText: "删除", cancelText: "取消", tone: "danger" });
    if (!ok) return;
    try {
      const result = await deleteVoiceoverTask(card.taskId);
      if (result.code !== 0) return toast.error(result.message || "删除失败");
      cards.outputCards.value = cards.outputCards.value.filter((item) => item.id !== card.id);
      cards.stopPollingCard(card.id);
      toast.success("音频已删除");
    } catch { toast.error("删除失败，请稍后重试"); }
  }

  onBeforeUnmount(() => runner.cleanup());
  return { settings, config, canGenerate, loadConfig, updateSettings, generate, removeCard, showNotice: (message) => toast.info(message), getModuleName: () => "AI配音", ...cards, ...runner, ...actions };
}
