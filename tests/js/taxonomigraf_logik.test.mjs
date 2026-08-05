// Tester för grafens skiktlogik. Körs med:  node --test tests/js/
//
// Filnamnet måste sluta på .test.mjs. Nodes inbyggda testlöpare plockar bara
// upp filer som matchar dess mönster (*.test.*, *-test.*, test-*, test.*);
// ett namn som test_taxonomigraf_logik.mjs samlas in som noll tester och
// rapporteras då grönt utan att ha kört någonting.
//
// Logikfilen är ett vanligt script utan export, eftersom webbläsaren laddar
// den som en <script>-tagg. Den utvärderas därför med new Function, som ger
// tillbaka funktionerna utan att filen behöver ett modulsystem.
//
// Avsiktligt INTE node:vm: en sandlåda är ett eget realm, och arrayer som
// skapas där har en annan Array-prototyp än testets. deepStrictEqual jämför
// prototyper och underkände då korrekta svar.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const kod = readFileSync(
  new URL("../../utils/static/taxonomigraf_logik.js", import.meta.url),
  "utf8",
);
// new Function på inläst text vore farligt om texten kom utifrån. Här är den
// projektets egen källfil, läst från en fast sökväg i repot, i en testfil som
// aldrig körs i drift. Ingen indata från användare eller nätverk når hit.
const { beraknaSkikt } = new Function(
  `${kod}\nreturn { beraknaSkikt, attlingar, forfader };`,
)();

// Ett litet träd med samma form som den riktiga taxonomin:
//   rot -> civilratt -> formogenhet -> obligation -> [AvtL]
//   rot -> offentlig
const NODER = [
  { id: "rot", foralder: "" },
  { id: "offentlig", foralder: "rot" },
  { id: "civilratt", foralder: "rot" },
  { id: "formogenhet", foralder: "civilratt" },
  { id: "obligation", foralder: "formogenhet" },
  { id: "avtl", foralder: "obligation" },
];

test("fokus omfattar noden och alla dess ättlingar", () => {
  const { fokus } = beraknaSkikt(NODER, "formogenhet");
  assert.deepEqual(new Set(fokus), new Set(["formogenhet", "obligation", "avtl"]));
});

test("kedjan går från roten ned till noden, i ordning", () => {
  const { kedja } = beraknaSkikt(NODER, "obligation");
  assert.deepEqual(kedja, ["rot", "civilratt", "formogenhet"]);
});

test("bakgrunden är exakt resten", () => {
  const { bakgrund } = beraknaSkikt(NODER, "formogenhet");
  assert.deepEqual(new Set(bakgrund), new Set(["offentlig"]));
});

test("fokus på roten lämnar ingen bakgrund", () => {
  const { fokus, kedja, bakgrund } = beraknaSkikt(NODER, "rot");
  assert.equal(fokus.length, NODER.length);
  assert.deepEqual(kedja, []);
  assert.deepEqual(bakgrund, []);
});

test("ett löv fokuserar bara sig självt", () => {
  const { fokus } = beraknaSkikt(NODER, "avtl");
  assert.deepEqual(fokus, ["avtl"]);
});

test("okänt id ger tom fokus och allt i bakgrunden", () => {
  const { fokus, bakgrund } = beraknaSkikt(NODER, "finns-inte");
  assert.deepEqual(fokus, []);
  assert.equal(bakgrund.length, NODER.length);
});

test("de tre skikten överlappar aldrig varandra", () => {
  const { fokus, kedja, bakgrund } = beraknaSkikt(NODER, "civilratt");
  const alla = [...fokus, ...kedja, ...bakgrund];
  assert.equal(new Set(alla).size, alla.length, "en nod hamnade i två skikt");
  assert.equal(alla.length, NODER.length, "alla noder ska tillhöra ett skikt");
});
