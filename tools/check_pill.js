// Checks pill.js's text patterns: hints and contact parsing on real BeyondATC lines, and speed on hostile
// input (a backtracking pattern once could hang the sim's UI). Run in CI: node tools/check_pill.js
"use strict";
const fs = require("fs");
const path = require("path");

const src = fs.readFileSync(path.join(__dirname, "..", "src", "html_ui", "paul-batc-pill", "pill.js"), "utf8");
function extract(from, to, name) {
  const a = src.indexOf(from), b = src.indexOf(to, a);
  if (a < 0 || b < 0) throw new Error("check_pill: can't find " + name + " in pill.js");
  return new Function(src.slice(a, b) + "; return " + name + ";")();
}
const readbackHint = extract("  var RWY", "  function clip", "readbackHint");
const contactIn = extract("  // A name is words", "  function onContact", "contactIn");

let failed = 0;
function expect(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) failed++;
  console.log((ok ? "ok   " : "FAIL ") + label + (ok ? "" : "\n     got  " + JSON.stringify(got) + "\n     want " + JSON.stringify(want)));
}

// hints, on ATC lines from live captures (2026-10-22)
const HINTS = [
  ["Airfrans 1234, Montpellier Ground, cleared to Marseille Provence via KELA8L departure, runway 12L, climb to FL060, squawk 1000.", "IFR clearance · Climb FL060"],
  ["Airfrans 1234, taxi via T1, hold short of runway 12L.", "Taxi via T1 · Hold short 12L"],
  ["Airfrans 1234, via T6 cross runway 12L, taxi to holding point T6, runway 12L, via T.", "Taxi 12L · Cross 12L"],
  ["Airfrans 1234, Montpellier Ground, pushback approved. Face south.", "Pushback · Face south"],
  ["Airfrans 1234, Montpellier Tower, wind 100 degrees, 5 knots, runway 12L, cleared for takeoff.", "Takeoff 12L"],
  ["Airfrans 1234, contact Montpellier Tower 118.775.", "Contact 118.775"],
  ["Wind 310 degrees, 8 knots.", ""],
  ["Airfrans 1234, readback correct. Call me back when ready for pushback or engine start.", ""],
  ["Airfrans 1234, Montpellier Ground?", ""],
  // 2026-10-23 flight (Player.log)
  ["Volotea 2NK, runway 30R, lineup and wait.", "Line up 30R"],
  ["Volotea 2NK, go around. Fly the published missed approach procedure, climb to 4,000.", "Go around · Climb 4000"],
  ["Volotea 2NK, reduce speed 270 kts.", "Speed 270"],
  ["Volotea 2NK, minimum approach speed.", "Min approach speed"],
  ["Volotea 2NK, resume normal speed.", "Normal speed"],
  ["Volotea 2NK, cleared MANA1D arrival, runway 21.", "STAR MANA1D"],
  ["Volotea 2NK, confirm new approach VORDME approach runway 21?", "Confirm VORDME 21"],
  ["Volotea 2NK, report ready for descent.", "Report ready for descent"],
  ["Volotea 2NK, taxi to Ramp 4L via A, R.", "Taxi to Ramp 4L"],
  ["Negative, taxi via M, T.", "Taxi via M, T"],
  ["Negative, QNH 1013.", "QNH 1013"],
  ["Volotea 2NK, unable direct at this time.", "Unable direct"],
  // 2026-10-23 sniffs (LFMT-LIRF, LIRF-)
  ["Volotea 5PK, Montpellier Ground, pushback and engine start approved. Face southeast.", "Pushback · Face southeast"],
  ["Volotea 6XB, SALIN is too far from your current position to allow safe sequencing. Unable direct SALIN at this time.", "Unable direct"],
  ["Aircraft calling for direct to, say callsign.", "Say callsign"],
  ["Volotea 5PK, roger, say fix name.", "Say fix name"],
  ["Volotea 5PK, say again gate number.", "Say gate number"],
  ["Volotea 5PK, exit right at DG.", "Exit right DG"],
  ["Negative, tower on 127.625.", "Contact 127.625"],
  ["Volotea 5PK, direct SUVOK, cleared ILS-X approach runway 16L.", "Approach 16L · Direct SUVOK"],
  ["Volotea 5PK, descend via STAR to 4,000, QNH 1019.", "Descend 4000 · QNH 1019"],
  ["Volotea 2NK, Nantes Tower, continue.", "Continue"],
  ["Volotea 2NK, welcome back. Continue.", "Continue"],
  ["Volotea 2NK, Bordeaux Control, identified, continue climb to FL380.", "Climb FL380"],
];
HINTS.forEach(([t, want]) => expect("hint    " + t.slice(0, 60), readbackHint(t), want));

const CONTACTS = [
  ["Airfrans 1234, contact Montpellier Tower 118.775, good day.", { name: "Montpellier Tower", freq: "118.775" }],
  ["Airfrans 1234, contact Tower when at runway hold point.", { name: "Tower", freq: "" }],
  ["contact Marseille Approach on 120.100", { name: "Marseille Approach", freq: "120.100" }],
  ["contact Montpellier Mediterranee UNICOM 122.800", { name: "Montpellier Mediterranee UNICOM", freq: "122.800" }],
  ["CONTACT MONTPELLIER TOWER WHEN READY", null],
];
CONTACTS.forEach(([t, want]) => expect("contact " + t.slice(0, 60), contactIn(t), want));

// "Frequencies:" as the toolbar's code reads it: listed in the order you call them; anything else kept raw
const parseFreqs = new Function(
  src.slice(src.indexOf("  function parseJson"), src.indexOf("  // Short hints")) +
  src.slice(src.indexOf('  // "Frequencies: ['), src.indexOf("  var GEAR")) + "; return parseFreqs;")();
expect("freqs   order and format", parseFreqs(JSON.stringify([
  { name: "Montpellier Tower (30R, 30L)", type: "Tower", frequency: "118.775", cpdlcLogonCode: "" },
  { name: "Marseille Control", type: "Center", frequency: 132.365, cpdlcLogonCode: "LFMM" },
  { name: "Montpellier Automated Terminal Information Service", type: "ATIS", frequency: "124.13" },
  { name: "Montpellier Ground", type: "Ground", frequency: "121.955" },
])).rows.map((r) => r.name + " " + r.freq),
  ["Montpellier ATIS 124.130", "Montpellier Ground 121.955", "Montpellier Tower 118.775", "Marseille Control 132.365"]);
expect("freqs   unreadable kept raw", parseFreqs("Nothing here"), { raw: "Nothing here" });

// speed: each must finish well under a frame budget even on long, unlucky input
const HOSTILE = [
  "contact " + "ABCDEFGHIJKLMNOPQRSTUVWXYZ".repeat(40) + " x",
  "contact " + "AB ".repeat(3000) + "x",
  "Airfrans 1234, contact " + "Montpellier Tower ".repeat(500) + "when ready.",
  "taxi " + "via T1 ".repeat(2000),
  "taxi via " + "T1, ".repeat(3000) + "hold",
  "report " + "ready ".repeat(2000),
  "cleared to " + "A ".repeat(3000),
  "CONTACT MONTPELLIER TOWER WHEN AT RUNWAY HOLD POINT ".repeat(100),
];
HOSTILE.forEach((t) => {
  const start = Date.now();
  readbackHint(t);
  contactIn(t);
  const ms = Date.now() - start;
  if (ms > 200) failed++;
  console.log((ms > 200 ? "FAIL " : "ok   ") + "speed   " + ms + " ms  " + t.slice(0, 50));
});

if (failed) {
  console.log(failed + " check(s) failed");
  process.exit(1);
}
