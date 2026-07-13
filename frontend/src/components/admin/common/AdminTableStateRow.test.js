// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AdminTableStateRow from "./AdminTableStateRow.vue";

function mountRow(props) {
  return mount({
    components: { AdminTableStateRow },
    template: "<table><tbody><AdminTableStateRow v-bind=\"props\" /></tbody></table>",
    setup: () => ({ props }),
  });
}

describe("AdminTableStateRow", () => {
  it("切换加载和空数据文案", () => {
    expect(mountRow({ loading: true, empty: false, colspan: 6 }).text()).toContain("加载中...");
    const empty = mountRow({ loading: false, empty: true, colspan: 8, emptyText: "暂无用户" });
    expect(empty.text()).toContain("暂无用户");
    expect(empty.get("td").attributes("colspan")).toBe("8");
  });
});
