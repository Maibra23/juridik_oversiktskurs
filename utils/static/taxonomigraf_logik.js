// Rena funktioner för Rättskartans grafinteraktion: vilka noder som hör till
// den fokuserade grenen, till kedjan upp mot roten, och till bakgrunden.
//
// Ingen DOM och inget vis-beroende, så att filen kan köras både i iframen
// (som <script>) och under node --test (via node:vm). Se
// tests/js/taxonomigraf_logik.test.mjs.

function byggForalderkarta(noder) {
  const karta = new Map();
  for (const nod of noder) {
    karta.set(nod.id, nod.foralder || "");
  }
  return karta;
}

function byggBarnkarta(noder) {
  const karta = new Map();
  for (const nod of noder) {
    if (!nod.foralder) continue;
    if (!karta.has(nod.foralder)) karta.set(nod.foralder, []);
    karta.get(nod.foralder).push(nod.id);
  }
  return karta;
}

// Noden själv plus hela dess delträd, i bredden först.
function attlingar(barnkarta, rotId) {
  const ut = [rotId];
  const ko = [rotId];
  while (ko.length) {
    const nuvarande = ko.shift();
    for (const barn of barnkarta.get(nuvarande) || []) {
      ut.push(barn);
      ko.push(barn);
    }
  }
  return ut;
}

// Kedjan från roten ned till nodens förälder, i den ordningen.
function forfader(foralderkarta, nodId) {
  const kedja = [];
  let nuvarande = foralderkarta.get(nodId);
  while (nuvarande) {
    kedja.unshift(nuvarande);
    nuvarande = foralderkarta.get(nuvarande);
  }
  return kedja;
}

// Tre skikt: fokus (grenen), kedja (vägen dit) och bakgrund (allt annat).
// Ett okänt id ger tom fokus och tom kedja, så att anroparen kan behandla
// det som "ingen fokusering" utan särfall.
function beraknaSkikt(noder, fokusId) {
  const foralderkarta = byggForalderkarta(noder);
  if (!foralderkarta.has(fokusId)) {
    return { fokus: [], kedja: [], bakgrund: noder.map((n) => n.id) };
  }
  const fokus = attlingar(byggBarnkarta(noder), fokusId);
  const kedja = forfader(foralderkarta, fokusId);
  const markerade = new Set([...fokus, ...kedja]);
  const bakgrund = noder.map((n) => n.id).filter((id) => !markerade.has(id));
  return { fokus: fokus, kedja: kedja, bakgrund: bakgrund };
}
