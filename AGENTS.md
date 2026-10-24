# Agent notes

MSFS 2024 community package (`paul-batc-pill`) that shows BeyondATC's comms state as a small pill in a
screen corner during flight, with a click-to-open settings card. Windows only. User docs:
[README.md](README.md).

## Layout

- `src/html_ui/paul-batc-pill/pill.js`: the whole runtime. WebSocket client for BeyondATC
  (`ws://127.0.0.1:41716`), state machine (`view()`), animated render (`render()` measures the new
  content, then transitions width), settings card, `CONFIG` defaults, and the comms section (messages under the
  pill, answers/requests on hover, Frequencies/Log panel). `pill.css`: the look; `--u` is
  one 1080p pixel times `CONFIG.scale`.
- `injections.json` + `tools/build.py`: the build copies the stock `MasterPage_InGame` cooked component
  from the local sim install, appends a hidden `<img onerror>` that loads `pill.js` once, and writes
  `layout.json` / `manifest.json`. `build | install | uninstall | lock | release [X.Y.Z]`.
  `stock.lock.json` holds the stock hash so `build` warns after sim updates.
- `config.json`: package metadata. Local paths (`sim_packages`, `community`) go in
  `.local/config.json`, which overrides it.
- `tools/inspect_ui.py`: Coherent inspector client (Devmode, `localhost:19999`); `--list`, `--page N`,
  `--push` hot-reloads the pill into mainUi (page 2). If it times out, a dead sim's child process may hold
  the port (seen: WinWing's SimAppPro2.exe): `netstat -ano | findstr 19999` shows a second LISTENING PID.
  `tools/sniff_batc.py`: socket logger; `tools/pill_log.py`: the pill's own flight log (builds from
  `build.py build`/`install` and `inspect_ui.py --push` set `CONFIG.devLog` and stream BeyondATC's messages,
  what the pill shows and what the user does to `ws://127.0.0.1:41799` while it runs; `release` doesn't;
  sniffer records plus `{"t","pill"}` / `{"t","event"}`; every command the pill sends is an event). Both write
  to `%LOCALAPPDATA%\paul-batc-pill\logs`. `tools/batc_timeline.py` prints either log as a timeline with
  `Actions`/`InfoBoxes` changes as diffs. `tools/harness.html`: desktop preview with replays, a fake
  `engine` and a "Hold PTT" button; `?fake` swaps in a socket that records what the pill sends (`batcPill.sent`).
- `docs/render/*.html` + `docs/render_images.py`: README/flightsim.to images via headless Edge (or
  Chrome/Chromium); `docs/render/pills.js` mirrors `view()`'s markup for the state sheet; `comms.html` runs the
  real pill.js on a recorded clearance through a stand-in socket (`?panel`: the Frequencies panel). Headless Chrome
  behind a proxy hangs on the Google Fonts link (it ignores HTTPS_PROXY): render with the proxy set, or offline.
  `docs/flightsim-to.md`: flightsim.to page text. `CHANGELOG.md`: release history.
- `.github/workflows/check.yml`: syntax checks, plus `tools/check_pill.js` (readback hints and contact parsing
  on real lines; pattern speed on hostile input). CI can't build without a sim install.
- `.local/` (git-ignored): local config, mockups, design prototypes, screenshots. Put new private files there.

## Sim facts (verified live)

- In-flight fullscreen UI is the `mainUi` view. `MasterPage_InGame` mounts there only in flight.
  `Toolbar_Trigger` renders in the toolbar's own small Panel.html view instead: don't hook it.
- Clicks reach an element only if the element directly under the cursor has `data-input-group` and
  computed `pointer-events` isn't `none` (mainUi inherits `none`). Mousemove arrives regardless.
  A click on no element of ours never reaches the page (a document `mousedown` listener saw nothing), so the
  open settings card closes on outside clicks through a transparent full-screen `#batc-pill-shade` with
  `data-input-group` (that click doesn't reach the sim; verified live 2026-10-23).
- `localStorage` is shared across all Coherent views; persistence across sim restarts is unverified.
- mainUi has no `SimVar`, `GetStoredData` or `Coherent`; VCockpit views (e.g. VLogic) have `SimVar`.
- mainUi fonts: only `Roboto-Regular` / `RobotoMono-Regular`; weights are synthesized.
- Avoid `gap`, `color-mix`, `backdrop-filter` in pill.css (Gameface).
- mainUi has `engine` (`on`/`off`/`trigger`/`call`) and can receive sim key events:
  `engine.trigger("ADD_VIEW_LISTENER", "JS_LISTENER_KEYEVENT", "/Global/mainUI.html")`, then
  `engine.call("INTERCEPT_KEY_EVENT", "<EVENT>", 0|1)` (1 also stops the sim acting on it; verified with
  `BAROMETRIC`) and `engine.on("keyIntercepted", (name, v0, v1, v2) => ...)`. Each event arrives twice in
  the same ms. A held key sends once, then every ~33 ms after ~0.4 s; release sends nothing. //42 Flow's
  mainUi hook uses the same `ADD_VIEW_LISTENER` route (for `JS_LISTENER_DATASTORAGE`).
- Controls > Communications > QUICK REPLY is `KEY_SR_COM_QUICK_REPLY` (`fs-input-profiles`), event
  `SR_COM_QUICK_REPLY`. Blocking it (1) by hand froze the sim; observed (0), it is never reported.
  `pill.js` refuses `SR_` events. The PTT indicator uses `TOGGLE_SPEAKER` (works live, observed with 0).
- No gamepads in mainUi (`navigator.getGamepads()` is `[]` even after presses). A package can't add new
  actions to the Controls menu (MSFS 2024 SDK: presets of existing actions only).
- Rounded `overflow: hidden` boxes had jagged corners in the sim while the unclipped settings card was
  smooth; the pill now clips square and draws its rounded background on `.bp-bg`. Corners still look
  jagged on light backgrounds: the outer borders are now a dark rim (`rgba(0, 0, 0, 0.1)`) to soften them;
  unverified in the sim.

## BeyondATC protocol

- Snapshot pushed on connect; several clients are fine. `CommsState: {"mode","text"}` modes seen:
  `ready`, `queued`, `processing`, `request`, `awaiting`, `speaking` (binary also has `waiting`,
  `controller`, `loading`, `download`, `turnaround`, `menu`).
- `traffic` (`ATC Generating`, then `ATC Transmitting`) carries `ATCTraffic:` broadcasts ("All aircraft
  be advised information Z now current").
- `speaking` is used for ATC and for the pilot TTS; the preceding `ATC:`/`ATCTraffic:`, `Player:` or
  `Traffic:` line says who.
- `Facility: Name (runways)|freq` or `Nothing Tuned`; `Com2: {label,frequency,monitor}`;
  `LoadState: {stage}` (`menu` in menus); `RadioMute: {com1,com2}`.
- `Actions: [Request IFR Clearance¬Wind Check¬...]`: the toolbar's menu, `¬`-separated. While ATC
  waits for you it offers `Say Again` (never in the request menu) with the replies: `Readback IFR
  Clearance¬Say Again¬`, `Acknowledge Instruction¬Say Again¬` (after "readback correct, call me back
  when ready"), `Cancel Runway Change¬Runway 12L¬Runway 12R¬Say Again¬` (after "say runway"). It keeps
  them until ATC confirms or moves on, and re-sends the menu after every transmission, so `pill.js`
  shows the hint only with a menu newer than the last speech (`menuFresh`) and not `answered` (a
  `Player:` line or `processing`/`request`/`queued` since ATC spoke). `QueuedAction` labels can be stale
  ("Say Again" while the pilot answers "Runway 12L"). Toolbar "Say Again" gives `Player: Say again, ...`.
  ATC chasing a missing reply: "Airfrans 1234, Montpellier Ground?", or the instruction again
  (`awaiting` with no queued request). BeyondATC drops taxi and acknowledge replies after ~18 s with no
  answer (menu back to requests, `pill.js` shows "No readback"); it keeps takeoff clearance and chases.
  A voice (PTT) reply is `processing` then `ready`, with no `Player:` line. `READBACKS` only shapes the hint.
  The same menu can span two exchanges: after a handoff's `Acknowledge Instruction¬Say Again¬`, your
  check-in and "Nantes Tower, continue." keep it unchanged, so `pill.js` treats an ATC line after your reply
  (or from a new station) as a new instruction, not a chase.
- `InfoBoxes: [{"title":"Taxi to Runway","info":"12L"},{"title":"SID","info":"KELA8L"},
  {"title":"Altitude Clearance","info":"FL060"},{"title":"Squawk","info":"1000"}]`: the toolbar's
  clearance boxes (`info` may hold `<br>`); `[]` at load, a CTAF box on UNICOM.
- `AutoTune: true|false`, `AutoRespond: true|false` (the toolbar switches). With Auto Tune off,
  `pill.js` keeps a "Contact" reminder from "contact <Station> [on] <freq>" until COM1 (`Facility`)
  matches. An `ATIS Current` box with a new letter shows "ATIS"; the snapshot's box doesn't.
  `CPDLCCode:` and other CPDLC traffic: the pill stays silent (CPDLC is fully handled in the sim).
- What the toolbar sends (its panel `beyondatc_toolbar.js`, BeyondATC's package, read 2026-10-23): `set_autotune: <bool>`,
  `set_autorespond: <bool>` on its switches, `set_action: <reply>` on a menu item, `set_frequency: <f>`,
  `frequencies` / `datis` / `atc_log` on tab clicks. BeyondATC broadcasts the resulting `AutoTune:` /
  `AutoRespond:` to every client (seen in sniffs when the toolbar switch was clicked).
- `AppError: {"text","fatal","kicked"}` (text may span lines; empty clears). `Callsign: {full,shortForm}`.
- The server pings (an empty frame); `sniff_batc.py` lost the connection after each one until it
  answered with a pong. Browsers pong on their own.
- A correct voice readback gets no answer from ATC: the toolbar just drops "Say Again" (`pill.js` shows
  "Readback OK" when that follows a reply). A wrong one gets "Negative, <correction>." with the menu kept
  (Player.log, 2026-10-23: 9 times in one flight). `Player.log` also has `[PilotSpeakState] ... waiting 10s for a
  player transcription | action=Acknowledge Instruction` after a voice exchange.
- Sniffs 2026-10-23 (LFMT-LIRF, LIRF-): a voice reply is `processing`, `ready`, then the request menu (no
  "Say Again"): accepted. After "Negative, ..." the same reply menu comes back unchanged. Checking in on a new
  frequency (`request` "Announce On Frequency"), BeyondATC flashes `Actions: [Say Callsign/Altitude¬Say Again¬]`
  for a few ms before ATC answers; `pill.js` ignores reply menus while `mode` is `request`/`processing`/`queued`.
  Right after an `Acknowledge Handoff` reply, BeyondATC retunes COM1 (`Facility`). Other types seen, unused:
  `Progress: {from,to,pct}`, `Settings: {...}` (BeyondATC's options), `CPDLC_ATC:` / `CPDLC_Pilot:`, `Wipe:`,
  `ToolbarVersion: 3.1`, `DATIS:` / `DATIS_END:`, `LoadState` stages `turnaround`, `download`.
- Unverified live: what `waiting` means. Whether "Say Again" leaves the menu after a voice reply the recogniser
  heard as nothing (`[VoiceRec] Empty final transcript ... Posting ParseFailed` in Player.log): ATC repeated the
  instruction each time so far, but if BeyondATC ever drops it instead, `pill.js` shows "Readback OK" wrongly.
- BeyondATC's own logs (`%userprofile%\AppData\LocalLow\Skirmish Mode Games, Inc\BeyondATC`):
  `Player.log` has every exchange as `[Instruction]` lines (ATC and pilot alike) and the script
  that handled it (`[ControllerScript] ...WindCheckScript`, `...IFR.IfrEvaluatorScript`), but no
  readback-expected state. Seen there: clearance "Airfrans 1234, Montpellier Ground, information D
  current, cleared to Marseille Provence via KELA8R departure, runway 30R, climb to 6000 feet, squawk
  1000.", toolbar readback, then "Airfrans 1234, readback correct. Call me back when ready for ...",
  then the pilot's "Wilco, Airfrans 1234.". `beyondATC.log` (CPDLC bridge) holds the Hoppie logon
  code: keep it private.
- Nothing is sent while PTT is held. The PTT indicator instead listens to a sim binding (below).
- `frequencies` gets `Frequencies: [{"name","type","frequency","cpdlcLogonCode"},...]` (from the toolbar's code; never
  in sniffs: BeyondATC sends it only when asked, maybe only to the asker): the stations around you (the toolbar
  heads it with one name), not the route; `type` is ATIS / Clearance / Ground / Tower / ApproachDeparture /
  Center / UNICOM. `pill.js` asks when the panel opens and when COM1 changes with Frequencies open, and files each
  reply under Departure or Arrival by `Progress: {from,to,pct}` (pct < 50: Departure). Without Progress the tab shows
  the last reply, no Departure / Arrival.
- Sniff digest (11 sniffs, 2026-10-22/23, incl. LFMT-LIRF 127 min): `Progress` pct is 0-100, from/to are ICAO, about
  once a minute in flight. No `Actions` request carries a parameter: requests that need one (direct-to fixes, arrival
  gates) get a follow-up reply menu once ATC asks. A command a client sends (toolbar, Auto Respond) is never echoed:
  it shows as `QueuedAction` + `queued`, then a `Player:` line. `CPDLCCode:` was empty in every sniff.
  Follow-up menus: "say fix name" gives `Cancel Direct Request¬<the route's fixes, repeats included>¬Say Again¬`
  (33 fixes), "say parking" `Allocated Gate¬Gate 301¬...¬Say Again¬` (74 gates), a STAR `Accept Clearance¬Request
  Different Runway¬Say Again¬`, a voice direct-to request "say callsign" `Say Callsign¬Say Again¬`. `pill.js` shows
  answers once each, Cancel last, three then "+N" (the opened list scrolls), and fills amber a readback,
  acknowledgement, "Accept", "Allocated" or a lone answer. Other menus seen: Acknowledge Cross Instruction /
  Takeoff Clearance / Landing Clearance / Handoff, Readback Instruction, `Acknowledge Instruction¬Ready for
  Descent¬Say Again¬`; requests Report Established, Declare Go Around, Report Clear of Runway, Request Taxi to
  (Assigned) Gate, Submit Turbulence / Icing Pirep, Call Ready for Descent, "Announce On/on Frequency" (both casings).
  While a flight loads: `LoadState` `loading` / `download` with text and pct, `Wipe:`, `RadioMute` true then false,
  and `Facility: 121.955|121.955` (the frequency as the name) before the station's. `DATIS: <ICAO>|<letter>|<text>`
  per airport in the snapshot, then `DATIS_END:`. On an ATIS frequency the menu is `Actions: []`.
- Comms panel, not yet verified live: the `Frequencies:` reply's exact values (`parseFreqs` shows anything it
  can't read raw); whether `set_frequency` sets COM1 active or standby (COM2 has no known command: right-click for COM2 is
  not built); what `atc_log` returns (not sent; the Log is built from the stream); whether wheel events reach
  mainUi (the Log scrolls); whether `set_action` from the pill (not the toolbar) is taken the same way.

## Rules

- Never commit Asobo files (cooked components, vanilla UI); the build copies them from the local install.
- Never commit design or prototype files (mockups, clickable prototypes): keep them in `.local/`.
- Never send anything on the BeyondATC socket except, on the user's click, the toolbar's own commands:
  `set_autotune: true|false`, `set_autorespond: true|false` (the hover buttons), and for the comms panel
  `set_action: <label>` (an answer or request, exactly as `Actions` lists it),
  `set_frequency: <f>`, and the tab requests `frequencies` / `atc_log`. WebSocket pongs aside.
- Changelogs and release notes list what changed, not why.
