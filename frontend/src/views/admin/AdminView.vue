<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import {
  Ban,
  CheckCircle2,
  Coins,
  LoaderCircle,
  ReceiptText,
  RefreshCw,
  Search,
  UsersRound,
} from "lucide-vue-next";
import {
  adjustAdminUserCredits,
  getAdminCreditOrders,
  getAdminCreditTransactions,
  getAdminOverview,
  getAdminUsers,
  updateAdminUser,
} from "@/api/admin.js";
import AppModal from "@/components/ui/AppModal.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

const tabs = [
  { key: "overview", label: "概览" },
  { key: "users", label: "用户" },
  { key: "orders", label: "订单" },
  { key: "transactions", label: "流水" },
];

const confirm = useConfirm();
const toast = useToast();

const activeTab = ref("overview");
const overview = ref(null);
const overviewLoading = ref(false);

const usersState = reactive({
  items: [],
  total: 0,
  page: 1,
  pageSize: 20,
  keyword: "",
  role: "",
  status: "",
  loading: false,
});

const ordersState = reactive({
  items: [],
  total: 0,
  page: 1,
  pageSize: 20,
  keyword: "",
  status: "",
  loading: false,
});

const transactionsState = reactive({
  items: [],
  total: 0,
  page: 1,
  pageSize: 20,
  keyword: "",
  type: "",
  loading: false,
});

const adjustModalOpen = ref(false);
const adjustTarget = ref(null);
const adjustSaving = ref(false);
const adjustForm = reactive({
  amount: "",
  note: "",
});

const overviewCards = computed(() => {
  const data = overview.value || {};
  return [
    { label: "用户总数", value: data.total_users || 0, icon: UsersRound },
    { label: "今日新增", value: data.today_new_users || 0, icon: CheckCircle2 },
    { label: "累计充值", value: formatMoney(data.paid_amount_cents || 0), icon: ReceiptText },
    { label: "今日充值", value: formatMoney(data.today_paid_amount_cents || 0), icon: Coins },
    { label: "总积分余额", value: `${data.total_credit_balance || 0} 点`, icon: Coins },
    { label: "失败任务", value: data.failed_image_tasks || 0, icon: Ban },
  ];
});

function formatMoney(amountCents) {
  return `¥${(Number(amountCents || 0) / 100).toFixed(2)}`;
}

function formatTime(value) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString("zh-CN", { hour12: false });
  } catch {
    return value;
  }
}

function roleLabel(role) {
  return role === "super_admin" ? "超级管理员" : "普通用户";
}

function statusLabel(status) {
  return status === "disabled" ? "已禁用" : "正常";
}

function transactionTypeLabel(type) {
  const map = {
    recharge: "充值",
    consume: "消费",
    refund: "退款",
    admin_adjust: "后台调整",
  };
  return map[type] || type || "-";
}

function totalPages(state) {
  return Math.max(1, Math.ceil(Number(state.total || 0) / Number(state.pageSize || 20)));
}

async function loadOverview() {
  overviewLoading.value = true;
  try {
    const result = await getAdminOverview();
    if (result.code !== 0) {
      toast.error(result.message || "加载概览失败");
      return;
    }
    overview.value = result.data || {};
  } catch {
    toast.error("加载概览失败");
  } finally {
    overviewLoading.value = false;
  }
}

async function loadUsers() {
  usersState.loading = true;
  try {
    const result = await getAdminUsers({
      page: usersState.page,
      page_size: usersState.pageSize,
      keyword: usersState.keyword || undefined,
      role: usersState.role || undefined,
      status: usersState.status || undefined,
    });
    if (result.code !== 0) {
      toast.error(result.message || "加载用户失败");
      return;
    }
    usersState.items = result.data?.items || [];
    usersState.total = result.data?.total || 0;
  } catch {
    toast.error("加载用户失败");
  } finally {
    usersState.loading = false;
  }
}

async function loadOrders() {
  ordersState.loading = true;
  try {
    const result = await getAdminCreditOrders({
      page: ordersState.page,
      page_size: ordersState.pageSize,
      keyword: ordersState.keyword || undefined,
      status: ordersState.status || undefined,
    });
    if (result.code !== 0) {
      toast.error(result.message || "加载订单失败");
      return;
    }
    ordersState.items = result.data?.items || [];
    ordersState.total = result.data?.total || 0;
  } catch {
    toast.error("加载订单失败");
  } finally {
    ordersState.loading = false;
  }
}

async function loadTransactions() {
  transactionsState.loading = true;
  try {
    const result = await getAdminCreditTransactions({
      page: transactionsState.page,
      page_size: transactionsState.pageSize,
      keyword: transactionsState.keyword || undefined,
      type: transactionsState.type || undefined,
    });
    if (result.code !== 0) {
      toast.error(result.message || "加载流水失败");
      return;
    }
    transactionsState.items = result.data?.items || [];
    transactionsState.total = result.data?.total || 0;
  } catch {
    toast.error("加载流水失败");
  } finally {
    transactionsState.loading = false;
  }
}

function loadActiveTab() {
  if (activeTab.value === "overview") loadOverview();
  if (activeTab.value === "users") loadUsers();
  if (activeTab.value === "orders") loadOrders();
  if (activeTab.value === "transactions") loadTransactions();
}

function applyUsersFilter() {
  usersState.page = 1;
  loadUsers();
}

function applyOrdersFilter() {
  ordersState.page = 1;
  loadOrders();
}

function applyTransactionsFilter() {
  transactionsState.page = 1;
  loadTransactions();
}

async function changeUserRole(user) {
  const nextRole = user.role === "super_admin" ? "user" : "super_admin";
  const ok = await confirm.open({
    title: nextRole === "super_admin" ? "设为超级管理员" : "取消超级管理员",
    message: `确定将 ${user.email} 设置为${roleLabel(nextRole)}吗？`,
    confirmText: "确认",
  });
  if (!ok) return;
  await saveUserPatch(user.id, { role: nextRole });
}

async function changeUserStatus(user) {
  const nextStatus = user.status === "disabled" ? "active" : "disabled";
  const ok = await confirm.open({
    title: nextStatus === "disabled" ? "禁用用户" : "启用用户",
    message: `确定${nextStatus === "disabled" ? "禁用" : "启用"} ${user.email} 吗？`,
    confirmText: nextStatus === "disabled" ? "禁用" : "启用",
    tone: nextStatus === "disabled" ? "danger" : "default",
  });
  if (!ok) return;
  await saveUserPatch(user.id, { status: nextStatus });
}

async function saveUserPatch(userId, payload) {
  try {
    const result = await updateAdminUser(userId, payload);
    if (result.code !== 0) {
      toast.error(result.message || "更新用户失败");
      return;
    }
    toast.success("用户已更新");
    await loadUsers();
    await loadOverview();
  } catch {
    toast.error("更新用户失败");
  }
}

function openAdjustModal(user) {
  adjustTarget.value = user;
  adjustForm.amount = "";
  adjustForm.note = "";
  adjustModalOpen.value = true;
}

async function submitAdjustCredits() {
  const amount = Number(adjustForm.amount);
  if (!Number.isInteger(amount) || amount === 0) {
    toast.error("请输入非 0 整数积分");
    return;
  }
  if (!adjustForm.note.trim()) {
    toast.error("请填写调整备注");
    return;
  }
  adjustSaving.value = true;
  try {
    const result = await adjustAdminUserCredits(adjustTarget.value.id, {
      amount,
      note: adjustForm.note.trim(),
    });
    if (result.code !== 0) {
      toast.error(result.message || "调整积分失败");
      return;
    }
    toast.success("积分已调整");
    adjustModalOpen.value = false;
    await loadUsers();
    await loadOverview();
    if (activeTab.value === "transactions") await loadTransactions();
  } catch {
    toast.error("调整积分失败");
  } finally {
    adjustSaving.value = false;
  }
}

function changePage(state, loader, direction) {
  const nextPage = state.page + direction;
  if (nextPage < 1 || nextPage > totalPages(state)) return;
  state.page = nextPage;
  loader();
}

watch(activeTab, () => {
  loadActiveTab();
});

onMounted(() => {
  loadOverview();
});
</script>

<template>
  <GeneratorLayout>
    <div class="flex flex-1 flex-col overflow-hidden">
      <header class="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div>
          <h1 class="text-base font-bold text-slate-800">管理后台</h1>
          <p class="text-xs text-slate-400">用户、充值订单和积分流水管理</p>
        </div>
        <button
          type="button"
          class="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          @click="loadActiveTab"
        >
          <RefreshCw class="h-3.5 w-3.5" />
          刷新
        </button>
      </header>

      <div class="border-b border-slate-200 bg-white px-6 pt-3">
        <nav class="flex gap-1 rounded-lg bg-slate-100 p-0.5 w-fit">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            class="rounded-md px-4 py-1.5 text-xs font-bold transition-all"
            :class="activeTab === tab.key ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <main class="flex-1 overflow-y-auto p-6">
        <section v-if="activeTab === 'overview'" class="space-y-5">
          <div v-if="overviewLoading" class="flex h-40 items-center justify-center text-sm text-slate-400">
            <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
            正在加载...
          </div>
          <div v-else class="grid gap-4 md:grid-cols-3">
            <div
              v-for="card in overviewCards"
              :key="card.label"
              class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div class="flex items-center justify-between">
                <p class="text-xs font-semibold text-slate-400">{{ card.label }}</p>
                <component :is="card.icon" class="h-4 w-4 text-primary" />
              </div>
              <p class="mt-3 text-2xl font-black text-slate-900">{{ card.value }}</p>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'users'" class="space-y-4">
          <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div class="flex min-w-64 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
              <Search class="h-4 w-4 text-slate-300" />
              <input
                v-model="usersState.keyword"
                type="text"
                class="w-full border-0 bg-transparent text-xs outline-none"
                placeholder="搜索邮箱或用户名"
                @keyup.enter="applyUsersFilter"
              />
            </div>
            <select v-model="usersState.role" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs" @change="applyUsersFilter">
              <option value="">全部角色</option>
              <option value="user">普通用户</option>
              <option value="super_admin">超级管理员</option>
            </select>
            <select v-model="usersState.status" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs" @change="applyUsersFilter">
              <option value="">全部状态</option>
              <option value="active">正常</option>
              <option value="disabled">已禁用</option>
            </select>
            <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="applyUsersFilter">
              查询
            </button>
            <span class="ml-auto text-xs text-slate-400">共 {{ usersState.total }} 个用户</span>
          </div>

          <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-50 text-slate-400">
                <tr>
                  <th class="px-4 py-3 font-semibold">用户</th>
                  <th class="px-4 py-3 font-semibold">角色</th>
                  <th class="px-4 py-3 font-semibold">状态</th>
                  <th class="px-4 py-3 font-semibold">积分</th>
                  <th class="px-4 py-3 font-semibold">注册时间</th>
                  <th class="px-4 py-3 text-right font-semibold">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="usersState.loading">
                  <td colspan="6" class="px-4 py-10 text-center text-slate-400">
                    <LoaderCircle class="mx-auto mb-2 h-5 w-5 animate-spin" />
                    加载中...
                  </td>
                </tr>
                <tr v-else-if="!usersState.items.length">
                  <td colspan="6" class="px-4 py-10 text-center text-slate-400">暂无用户</td>
                </tr>
                <tr v-for="user in usersState.items" v-else :key="user.id" class="border-t border-slate-100">
                  <td class="px-4 py-3">
                    <p class="font-bold text-slate-800">{{ user.email }}</p>
                    <p class="mt-0.5 text-slate-400">ID {{ user.id }} · {{ user.username }}</p>
                  </td>
                  <td class="px-4 py-3">
                    <span class="rounded-full px-2 py-1 text-[11px] font-bold" :class="user.role === 'super_admin' ? 'bg-primary/10 text-primary' : 'bg-slate-100 text-slate-500'">
                      {{ roleLabel(user.role) }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <span class="rounded-full px-2 py-1 text-[11px] font-bold" :class="user.status === 'disabled' ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'">
                      {{ statusLabel(user.status) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 font-black text-primary">{{ user.credits }} 点</td>
                  <td class="px-4 py-3 text-slate-500">{{ formatTime(user.created_at) }}</td>
                  <td class="px-4 py-3">
                    <div class="flex justify-end gap-2">
                      <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="openAdjustModal(user)">
                        调积分
                      </button>
                      <button type="button" class="rounded-lg border border-slate-200 px-2.5 py-1.5 font-semibold text-slate-600 hover:bg-slate-50" @click="changeUserRole(user)">
                        {{ user.role === 'super_admin' ? '取消超管' : '设为超管' }}
                      </button>
                      <button type="button" class="rounded-lg border px-2.5 py-1.5 font-semibold" :class="user.status === 'disabled' ? 'border-emerald-200 text-emerald-600 hover:bg-emerald-50' : 'border-rose-200 text-rose-600 hover:bg-rose-50'" @click="changeUserStatus(user)">
                        {{ user.status === 'disabled' ? '启用' : '禁用' }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex items-center justify-center gap-3 text-xs text-slate-500">
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40" :disabled="usersState.page <= 1" @click="changePage(usersState, loadUsers, -1)">上一页</button>
            <span>{{ usersState.page }} / {{ totalPages(usersState) }}</span>
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40" :disabled="usersState.page >= totalPages(usersState)" @click="changePage(usersState, loadUsers, 1)">下一页</button>
          </div>
        </section>

        <section v-else-if="activeTab === 'orders'" class="space-y-4">
          <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <input v-model="ordersState.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索邮箱或订单号" @keyup.enter="applyOrdersFilter" />
            <select v-model="ordersState.status" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs" @change="applyOrdersFilter">
              <option value="">全部状态</option>
              <option value="pending">待支付</option>
              <option value="paid">已支付</option>
              <option value="failed">失败</option>
            </select>
            <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="applyOrdersFilter">查询</button>
            <span class="ml-auto text-xs text-slate-400">共 {{ ordersState.total }} 个订单</span>
          </div>

          <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-50 text-slate-400">
                <tr>
                  <th class="px-4 py-3 font-semibold">订单</th>
                  <th class="px-4 py-3 font-semibold">用户</th>
                  <th class="px-4 py-3 font-semibold">套餐</th>
                  <th class="px-4 py-3 font-semibold">金额</th>
                  <th class="px-4 py-3 font-semibold">状态</th>
                  <th class="px-4 py-3 font-semibold">时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="ordersState.loading">
                  <td colspan="6" class="px-4 py-10 text-center text-slate-400">加载中...</td>
                </tr>
                <tr v-else-if="!ordersState.items.length">
                  <td colspan="6" class="px-4 py-10 text-center text-slate-400">暂无订单</td>
                </tr>
                <tr v-for="order in ordersState.items" v-else :key="order.id" class="border-t border-slate-100">
                  <td class="px-4 py-3">
                    <p class="font-bold text-slate-800">{{ order.out_trade_no }}</p>
                    <p class="mt-0.5 text-slate-400">{{ order.provider_trade_no || '-' }}</p>
                  </td>
                  <td class="px-4 py-3 text-slate-600">{{ order.user_email || order.user_id }}</td>
                  <td class="px-4 py-3">
                    <p class="font-bold text-slate-800">{{ order.package_name }}</p>
                    <p class="mt-0.5 text-primary">{{ order.credits }} 点</p>
                  </td>
                  <td class="px-4 py-3 font-bold text-slate-800">{{ formatMoney(order.amount_cents) }}</td>
                  <td class="px-4 py-3 text-slate-600">{{ order.status }}</td>
                  <td class="px-4 py-3 text-slate-500">{{ formatTime(order.paid_at || order.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex items-center justify-center gap-3 text-xs text-slate-500">
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40" :disabled="ordersState.page <= 1" @click="changePage(ordersState, loadOrders, -1)">上一页</button>
            <span>{{ ordersState.page }} / {{ totalPages(ordersState) }}</span>
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40" :disabled="ordersState.page >= totalPages(ordersState)" @click="changePage(ordersState, loadOrders, 1)">下一页</button>
          </div>
        </section>

        <section v-else class="space-y-4">
          <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <input v-model="transactionsState.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索邮箱或备注" @keyup.enter="applyTransactionsFilter" />
            <select v-model="transactionsState.type" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs" @change="applyTransactionsFilter">
              <option value="">全部类型</option>
              <option value="recharge">充值</option>
              <option value="consume">消费</option>
              <option value="refund">退款</option>
              <option value="admin_adjust">后台调整</option>
            </select>
            <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="applyTransactionsFilter">查询</button>
            <span class="ml-auto text-xs text-slate-400">共 {{ transactionsState.total }} 条流水</span>
          </div>

          <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table class="w-full text-left text-xs">
              <thead class="bg-slate-50 text-slate-400">
                <tr>
                  <th class="px-4 py-3 font-semibold">用户</th>
                  <th class="px-4 py-3 font-semibold">类型</th>
                  <th class="px-4 py-3 font-semibold">变动</th>
                  <th class="px-4 py-3 font-semibold">余额</th>
                  <th class="px-4 py-3 font-semibold">备注</th>
                  <th class="px-4 py-3 font-semibold">时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="transactionsState.loading">
                  <td colspan="6" class="px-4 py-10 text-center text-slate-400">加载中...</td>
                </tr>
                <tr v-else-if="!transactionsState.items.length">
                  <td colspan="6" class="px-4 py-10 text-center text-slate-400">暂无流水</td>
                </tr>
                <tr v-for="tx in transactionsState.items" v-else :key="tx.id" class="border-t border-slate-100">
                  <td class="px-4 py-3 text-slate-600">{{ tx.user_email || tx.user_id }}</td>
                  <td class="px-4 py-3">{{ transactionTypeLabel(tx.type) }}</td>
                  <td class="px-4 py-3 font-black" :class="tx.credits_delta >= 0 ? 'text-emerald-600' : 'text-rose-600'">
                    {{ tx.credits_delta >= 0 ? '+' : '' }}{{ tx.credits_delta }}
                  </td>
                  <td class="px-4 py-3 font-bold text-slate-800">{{ tx.balance_after }} 点</td>
                  <td class="px-4 py-3 text-slate-500">{{ tx.note || '-' }}</td>
                  <td class="px-4 py-3 text-slate-500">{{ formatTime(tx.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex items-center justify-center gap-3 text-xs text-slate-500">
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40" :disabled="transactionsState.page <= 1" @click="changePage(transactionsState, loadTransactions, -1)">上一页</button>
            <span>{{ transactionsState.page }} / {{ totalPages(transactionsState) }}</span>
            <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40" :disabled="transactionsState.page >= totalPages(transactionsState)" @click="changePage(transactionsState, loadTransactions, 1)">下一页</button>
          </div>
        </section>
      </main>

      <AppModal :open="adjustModalOpen" title="调整积分" subtitle="必须填写备注，操作会写入积分流水和审计日志" @close="adjustModalOpen = false">
        <div class="space-y-4 p-5">
          <div v-if="adjustTarget" class="rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-600">
            <p class="font-bold text-slate-800">{{ adjustTarget.email }}</p>
            <p class="mt-1">当前余额：{{ adjustTarget.credits }} 点</p>
          </div>
          <label class="block">
            <span class="text-xs font-bold text-slate-600">调整积分</span>
            <input v-model="adjustForm.amount" type="number" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" placeholder="正数加积分，负数扣积分" />
          </label>
          <label class="block">
            <span class="text-xs font-bold text-slate-600">备注</span>
            <textarea v-model="adjustForm.note" rows="3" class="mt-1 w-full resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" placeholder="例如：客服补偿、异常扣回"></textarea>
          </label>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="adjustModalOpen = false">取消</button>
            <button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="adjustSaving" @click="submitAdjustCredits">
              {{ adjustSaving ? '保存中...' : '确认调整' }}
            </button>
          </div>
        </div>
      </AppModal>
    </div>
  </GeneratorLayout>
</template>
