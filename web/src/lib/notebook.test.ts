// Run: npm test --prefix web   (Node's built-in test runner, no extra packages)
import assert from "node:assert/strict";
import { test } from "node:test";
import { cellKey, deriveAutoMarks, type Group, type Marks } from "./notebook.ts";

const suspects = ["Priya", "Jordan", "Leo"];
const groups: Group[] = [
  { name: "Room", values: ["Porch", "Loft", "Sunroom"] },
  { name: "Time", values: ["7:00 PM", "7:30 PM", "8:00 PM"] },
];
const k = cellKey;

test("one ✓ rules out the rest of its row group and its column", () => {
  const auto = deriveAutoMarks({ [k("Priya", "Sunroom")]: "yes" }, suspects, groups);
  assert.deepEqual(
    [...auto].sort(),
    [k("Jordan", "Sunroom"), k("Leo", "Sunroom"), k("Priya", "Loft"), k("Priya", "Porch")].sort(),
  );
  // Other groups of the same suspect are untouched.
  assert.equal(auto.has(k("Priya", "7:00 PM")), false);
});

test("two conflicting ✓ in one row: nothing crashes, no extra ✓, both stay manual", () => {
  const marks: Marks = { [k("Priya", "Porch")]: "yes", [k("Priya", "Loft")]: "yes" };
  const auto = deriveAutoMarks(marks, suspects, groups);
  // Each ✓ marks the other as automatic; the manual ✓ still wins when rendering.
  assert.equal(auto.has(k("Priya", "Sunroom")), true);
  assert.equal(auto.has(k("Jordan", "Porch")), true);
  assert.equal(auto.has(k("Leo", "Loft")), true);
  assert.equal(Object.values(marks).filter((m) => m === "yes").length, 2);
});

test("removing the ✓ removes its automatic marks", () => {
  assert.equal(deriveAutoMarks({ [k("Priya", "Sunroom")]: "" }, suspects, groups).size, 0);
  assert.equal(deriveAutoMarks({}, suspects, groups).size, 0);
});

test("a manual ✗ under an automatic one stays manual, and ✗ alone derives nothing", () => {
  const marks: Marks = { [k("Priya", "Sunroom")]: "yes", [k("Jordan", "Sunroom")]: "no" };
  const auto = deriveAutoMarks(marks, suspects, groups);
  assert.equal(auto.has(k("Jordan", "Sunroom")), true); // also automatic…
  assert.equal(marks[k("Jordan", "Sunroom")], "no"); // …but the manual mark is what is stored
  assert.equal(deriveAutoMarks({ [k("Leo", "Loft")]: "no" }, suspects, groups).size, 0);
});
