import { test } from "node:test";
import assert from "node:assert/strict";
import { calculate, example, parseReadings } from "../../app/lib/corrosion.ts";
const close = (actual, expected) =>
  assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`);
test("Faraday fixture and proportional response", () => {
  const d = { ...example, method: "current" };
  close(calculate(d).rate, 0.1160894790343075);
  close(calculate({ ...d, current: "20" }).rate, calculate(d).rate * 2);
});
test("Stern–Geary uses independent slopes, no hidden current input", () => {
  const r = calculate({ ...example, method: "lpr", current: "" });
  close(r.current, (120 * 120) / (2.303 * 240));
});
test("Coupon conversion and cleaning subtraction", () => {
  const d = { ...example, method: "coupon" };
  close(calculate(d).rate, (87.6 * 100) / (7.87 * 10 * 168));
  close(calculate({ ...d, cleaning: "50" }).rate, calculate(d).rate / 2);
  assert.throws(() => calculate({ ...d, cleaning: "101" }));
});
test("Thickness trend sorts inputs and resolves known rate", () => {
  const r = calculate({
    ...example,
    readings: "date,thickness_mm\n2023-01-01,7.4\n2020-01-02,8",
    tolerance: "0",
  });
  close(r.rate, 0.2);
  close(r.yearsToMinimum, 12);
});
test("Zero/increasing trends abstain from finite life", () => {
  for (const t of ["8", "8.2"])
    assert.equal(
      calculate({ ...example, readings: `date,thickness_mm\n2024-01-01,8\n2025-01-01,${t}` })
        .yearsToMinimum,
      null,
    );
});
test("Unsupported mechanisms and invalid inputs fail explicitly", () => {
  for (const d of [
    { mechanism: "pitting" },
    { method: "current", density: "0" },
    { method: "coupon", hours: "NaN" },
    { method: "lpr", resistance: "" },
    { minimum: "Infinity" },
  ])
    assert.throws(() => calculate({ ...example, ...d }));
});
test("Date/CSV validation catches ambiguous measurements", () => {
  for (const csv of [
    "date,thickness_mm\n2024-02-30,8\n2025-01-01,7",
    "date,thickness_mm\n2024-01-01,8\n2024-01-01,7",
    "date,thickness_mm\n2024-01-01,8,9\n2025-01-01,7",
  ])
    assert.throws(() => parseReadings(csv));
});
test("Reached threshold remains zero time regardless of fitted sign", () => {
  assert.equal(calculate({ ...example, minimum: "8" }).yearsToMinimum, 0);
});
