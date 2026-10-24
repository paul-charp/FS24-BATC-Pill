# flightsim.to page

Main image: `docs/images/splash.png` (1920x1080). Gallery: `docs/images/comms.png`, `docs/images/panel.png`,
`docs/images/states.png`, `docs/images/settings.png`.

## Title

BATC Comms Pill (BeyondATC radio status, messages and replies)

## Keywords

BeyondATC, BATC, ATC, radio, comms, status, indicator, overlay, HUD, UI, toolbar, notification, readback, subtitles, COM1, COM2, frequency, MSFS 2024, utility

## Short description

A small, quiet pill in a corner of the screen that shows what BeyondATC is doing on the radio, with ATC's messages under it and your answers, requests and frequencies one hover or click away.

## Description

A small, quiet pill in a corner of the screen that shows what BeyondATC is doing on the radio, and does what the BeyondATC toolbar does around it, so you can keep the toolbar closed.

**Messages, answers and requests**
- ATC's messages (and yours) show under the pill. An exchange's messages leave together once it's over; AI traffic's can be shown too
- Hover the message ATC waits on, or the pill, and its answers open below it: one click to read back, acknowledge or answer a question
- With nothing pending, hover the pill for BeyondATC's requests (clearance, push, taxi, direct to, ...)
- With Auto Tune off, "Tune" sets COM1 to the station ATC handed you to
- Click the pill for a panel with the frequencies (Departure / Arrival) and the radio log
- In the bottom corners everything stacks upward; in the left corners it's mirrored

**What it shows**
- Queued, Processing and Awaiting ATC while your request is on its way
- ATC talking, with the station and frequency (amber)
- Awaiting readback / Awaiting response: what ATC is waiting for from you, as a short hint ("Taxi via T1 · Hold short 12L"), the clearance values or the toolbar's clearance boxes. Red-orange when ATC calls you again or answers "Negative" with a correction, green when ATC takes your reply, and "No readback" if BeyondATC gives up waiting
- Transmitting, while your readback or request plays (green), and optionally while you hold PTT, with the hint of the readback you're answering
- Radio changes: the new station when COM1 or COM2 changes (cyan), and with Auto Tune off, whom to contact
- A new ATIS letter, ATC calling while COM1 is muted, AI traffic talking, and BeyondATC offline

When nothing is happening it shrinks to a small dot. Changes between states are animated.

**Settings**
Hover the pill for two buttons that flip BeyondATC's Auto Tune and Auto Respond. Click the pill, then the gear in its panel, to open the settings (a click outside closes them): which events and messages to show and how much detail (Display tab), corner, position and size (Position tab).

**Requirements**
- Microsoft Flight Simulator 2024
- BeyondATC 3.x desktop app (the toolbar panel doesn't need to be open)

**Installation**
Extract the `paul-batc-pill` folder into your Community folder.

**Notes**
- The pill reads BeyondATC's local connection. It only sends what the toolbar sends, when you click: an answer or request, a frequency, the frequency list, and Auto Tune / Auto Respond.
- Optional PTT indicator: bind your PTT button a second time to the sim's Toggle Speaker (Controls > Communications), keeping BeyondATC's binding, then turn it on in the settings.
- CPDLC is left to the sim's own datalink pages.
- The mod overrides one stock UI component (`MasterPage_InGame`) to load. Another mod that overrides the same component will conflict with it. After a sim update that changes it, install the updated version.
- Not affiliated with BeyondATC or Microsoft.

Source and issues: https://github.com/paul-charp/FS24-BATC-Pill

## Changelog

2.0.0

Reply to ATC and make requests from the pill, without BeyondATC's toolbar.

- Added: ATC's messages appear under the pill. Choose Off, Mine (only your conversations) or All.
- Added: hover the pill or the message ATC is waiting on to see your possible answers.
- Added: hover the pill when the radio is quiet to see the requests you can make.
- Added: with Auto Tune off, a "Tune" button sets COM1 to the next station after a handoff.
- Added: click the pill to open the Frequencies and Log panel.
- Added: Auto Tune and Auto Respond buttons next to the pill.
- Added: readback hints. When ATC waits for your reply, the pill says so and shows what to read back: a short hint, the values, or the clearance boxes.
- Added: the pill turns red-orange when ATC calls you again ("×2", "×3"), when ATC corrects a wrong readback ("Negative"), and when ATC calls you while COM1 is muted.
- Added: "No readback" when BeyondATC gives up waiting for your reply.
- Added: "Readback OK" in green when ATC accepts your reply.
- Added: optional "Keep last clearance", which keeps your last clearance on the pill, dimmed.
- Added: a "Contact" reminder when Auto Tune is off and ATC hands you to another station.
- Added: new ATIS letters, and "ATIS" while one plays on COM1.
- Added: optional PTT indicator, which turns red-orange if you talk over ATC or traffic.
- Changed: "You" is now "Transmitting".
- Changed: settings are split into Display and Position tabs, and open from the gear in the panel.
- Changed: the sample pill in the settings shows what your last change does.
- Changed: a softer, darker edge around the pill and its panels.
- Fixed: the idle dot stayed on screen in the sim's menus after a flight.
- Fixed: BeyondATC errors showed as raw code.
- Fixed: ATC broadcasts to all aircraft showed "ATC Generating" / "ATC Transmitting".
- Fixed: an ATIS on COM1 showed as "Traffic" or "Service".
- Fixed: radio changes showed while a flight was loading.

1.0.1

- Fixed: the pill stretched across the whole screen at startup when BeyondATC wasn't running.

1.0.0

- First release.
