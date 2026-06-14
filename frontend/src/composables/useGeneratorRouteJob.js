import { onMounted, watch } from "vue";
import { deleteGenerationJob } from "@/api/generation.js";

export function useGeneratorRouteJob({ generator, route, router, basePath, toast, confirm }) {
  async function openHistory() {
    generator.showHistoryDrawer.value = true;
    await generator.loadHistoryTasks();
  }

  function pickHistory(jobId) {
    generator.showHistoryDrawer.value = false;
    router.push(`${basePath}/${jobId}`);
  }

  async function handleCreateNewTask() {
    const ok = await generator.createNewTask();
    if (ok) {
      router.push(basePath);
    }
  }

  async function handleRouteJobId(jobId) {
    if (jobId && jobId !== generator.currentJobId.value) {
      const ok = await generator.loadGenerationJob(jobId);
      if (!ok) {
        router.replace(basePath);
      }
    } else if (!jobId && generator.currentJobId.value) {
      generator.resetWorkspaceToDraft();
    }
  }

  async function handleDeleteJob(job) {
    const displayStatus = job.display_status || job.status;
    if (displayStatus === "generating") {
      toast.info("任务生成中，暂不能删除");
      return;
    }

    const ok = await confirm.open({
      title: "删除任务",
      message: "确定删除这个生成任务吗？已生成图片不会立即从存储中物理删除。",
      confirmText: "删除",
      cancelText: "取消",
      tone: "danger",
    });
    if (!ok) return;

    try {
      const res = await deleteGenerationJob(job.job_id);
      if (res.code !== 0) {
        toast.error(res.message || "删除失败");
        return;
      }

      const idx = generator.historyTasks.value.findIndex((t) => t.job_id === job.job_id);
      if (idx > -1) generator.historyTasks.value.splice(idx, 1);
      if (job.job_id === generator.currentJobId.value) {
        generator.resetWorkspaceToDraft();
        router.push(basePath);
      }
      toast.success("任务已删除");
    } catch {
      toast.error("删除失败，请稍后重试");
    }
  }

  onMounted(() => {
    const jobId = route.params.jobId;
    if (jobId) {
      handleRouteJobId(jobId);
    }
  });

  watch(
    () => route.params.jobId,
    (newJobId) => {
      handleRouteJobId(newJobId);
    },
  );

  return {
    openHistory,
    pickHistory,
    handleCreateNewTask,
    handleDeleteJob,
  };
}
