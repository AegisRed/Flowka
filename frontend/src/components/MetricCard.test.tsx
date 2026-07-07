import { render, screen } from "@testing-library/react";
import { Activity } from "lucide-react";
import { describe, expect, it } from "vitest";

import { MetricCard } from "./MetricCard";

describe("MetricCard", () => {
  it("renders metric content", () => {
    render(<MetricCard detail="live stream" icon={Activity} title="Messages" value="24/s" />);

    expect(screen.getByText("Messages")).toBeInTheDocument();
    expect(screen.getByText("24/s")).toBeInTheDocument();
    expect(screen.getByText("live stream")).toBeInTheDocument();
  });
});

