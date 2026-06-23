import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import StatusBadge from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders the status name", () => {
    const { getByText } = render(<StatusBadge status="PENDING" />);
    expect(getByText("PENDING")).toBeInTheDocument();
  });

  it("uses different classes for terminal states", () => {
    const { getByText: completed } = render(<StatusBadge status="COMPLETED" />);
    const { getByText: rejected } = render(<StatusBadge status="REJECTED" />);
    expect(completed("COMPLETED").className).not.toEqual(rejected("REJECTED").className);
  });
});
