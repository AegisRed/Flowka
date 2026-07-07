import { describe, expect, it } from "vitest";

import { compactNumber, statusLabel } from "./status";

describe("status helpers", () => {
  it("maps API statuses to UI labels", () => {
    expect(statusLabel("healthy")).toBe("Healthy");
    expect(statusLabel("warning")).toBe("Warning");
  });

  it("compacts large operational numbers", () => {
    expect(compactNumber(12_400)).toBe("12.4K");
    expect(compactNumber(87)).toBe("87");
  });
});

