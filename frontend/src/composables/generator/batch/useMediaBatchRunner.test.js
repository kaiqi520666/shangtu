import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useMediaBatchRunner } from "./useMediaBatchRunner.js";

const api = vi.hoisted(() => ({
  createGenerationJob: vi.fn(),
  updateGenerationJob: vi.fn(),
}));

vi.mock("@/api/generation.js", () => ({
  createGenerationJob: api.createGenerationJob,
  getGenerationJob: vi.fn(),
  listGenerationJobs: vi.fn(),
  updateGenerationJob: api.updateGenerationJob,
}));

function createCards() {
  return {
    outputCards: ref([]),
    genLogs: ref([]),
    creatingBatch: ref(false),
    generating: ref(false),
    activeBatchRunId: ref(""),
    startPollingCard: vi.fn(),
    clearAllPollTimers: vi.fn(),
    trackBatch: vi.fn(),
    maybeFinishGenerating: vi.fn(),
    makeId: vi.fn(() => "batch-1"),
    TERMINAL_STATUSES: new Set(["done", "failed", "timeout"]),
  };
}

function enqueue(runner, createTask, queue = [{ id: "first" }]) {
  return runner.enqueueMediaBatch({
    queue,
    snapshotPayload: { settings: {} },
    createCard: ({ item, sortOrder, batchRunId }) => ({
      id: item.id,
      taskId: "",
      status: "pending",
      errorMessage: "",
      strategyTitle: item.id,
      sortOrder,
      batchRunId,
    }),
    createTask,
    preferCreateErrorAsToast: true,
  });
}

describe("useMediaBatchRunner enqueueMediaBatch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.createGenerationJob.mockResolvedValue({
      code: 0,
      data: { job_id: "job-1", title: "新任务" },
    });
    api.updateGenerationJob.mockResolvedValue({ code: 0 });
  });

  it("在生成接口返回前就插入卡片，成功后绑定 task_id 并轮询", async () => {
    let resolveTask;
    const createTask = vi.fn(() => new Promise((resolve) => {
      resolveTask = resolve;
    }));
    const cards = createCards();
    const runner = useMediaBatchRunner({ cards, scenario: "test", toast: { info: vi.fn(), error: vi.fn() } });

    const batchPromise = enqueue(runner, createTask);
    await vi.waitFor(() => expect(createTask).toHaveBeenCalledOnce());

    expect(cards.outputCards.value).toHaveLength(1);
    expect(cards.outputCards.value[0].taskId).toBe("");
    expect(cards.trackBatch).toHaveBeenCalledWith("batch-1");

    resolveTask({ code: 0, data: { task_id: "task-1", credit_cost: 3 } });
    await expect(batchPromise).resolves.toBe(true);
    expect(cards.outputCards.value[0]).toMatchObject({ taskId: "task-1", creditCost: 3 });
    expect(cards.startPollingCard).toHaveBeenCalledWith(cards.outputCards.value[0]);
  });

  it.each([
    ["业务失败", () => Promise.resolve({ code: 1, message: "余额不足" }), "余额不足"],
    ["缺少 task_id", () => Promise.resolve({ code: 0, data: {} }), "任务创建失败：后端未返回任务 ID"],
    ["网络异常", () => Promise.reject(new Error("offline")), "任务创建失败"],
  ])("%s 时保留失败卡片", async (_name, createTask, errorMessage) => {
    const cards = createCards();
    const toast = { info: vi.fn(), error: vi.fn() };
    const runner = useMediaBatchRunner({ cards, scenario: "test", toast });

    await expect(enqueue(runner, createTask)).resolves.toBe(false);

    expect(cards.outputCards.value[0]).toMatchObject({
      status: "failed",
      errorMessage,
    });
    expect(cards.startPollingCard).not.toHaveBeenCalled();
    expect(cards.maybeFinishGenerating).toHaveBeenCalledWith("batch-1", { silent: true });
    expect(toast.error).toHaveBeenCalledWith(errorMessage);
  });

  it("批量部分失败时仅轮询成功卡片并正常结束提交", async () => {
    const createTask = vi.fn()
      .mockResolvedValueOnce({ code: 0, data: { task_id: "task-1" } })
      .mockResolvedValueOnce({ code: 1, message: "创建失败" });
    const cards = createCards();
    const runner = useMediaBatchRunner({ cards, scenario: "test", toast: { info: vi.fn(), error: vi.fn() } });

    await expect(enqueue(runner, createTask, [{ id: "first" }, { id: "second" }])).resolves.toBe(true);

    expect(cards.outputCards.value).toHaveLength(2);
    expect(cards.outputCards.value.find((card) => card.id === "first").taskId).toBe("task-1");
    expect(cards.outputCards.value.find((card) => card.id === "second")).toMatchObject({
      status: "failed",
      errorMessage: "创建失败",
    });
    expect(cards.startPollingCard).toHaveBeenCalledOnce();
    expect(cards.maybeFinishGenerating).toHaveBeenCalledWith("batch-1");
  });
});
