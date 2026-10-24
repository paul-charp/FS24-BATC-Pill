// Pill markup for the doc renders, matching pill.js view().
var BP = (function () {
  var LAMP = '<span class="bp-lamp"></span>';
  var DOTS = '<span class="bp-dots"><i></i><i></i><i></i></span>';
  var BARS = '<span class="bp-bars"><i></i><i></i><i></i><i></i></span>';
  var RADIO = '<svg class="bp-ico bp-radio" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" ' +
    'stroke-linecap="round"><circle cx="8" cy="8" r="1.6" fill="currentColor" stroke="none"/>' +
    '<path d="M5.2 5.2a4 4 0 0 0 0 5.6M10.8 5.2a4 4 0 0 1 0 5.6M3.1 3.1a7 7 0 0 0 0 9.8M12.9 3.1a7 7 0 0 1 0 9.8"/></svg>';
  var MIC = '<svg class="bp-ico bp-mic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" ' +
    'stroke-linecap="round"><rect x="5.5" y="1.5" width="5" height="8.5" rx="2.5" fill="currentColor" stroke="none"/>' +
    '<path d="M3 8a5 5 0 0 0 10 0M8 13v2"/></svg>';
  var MUTE = '<svg class="bp-ico" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" ' +
    'stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h2l3-2.5v9L5 10H3z"/><path d="M11 6l3.5 4M14.5 6L11 10"/></svg>';
  var CHECK = '<svg class="bp-ico bp-check" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 8.5l3 3 6-6.5"/></svg>';
  var KEPT = '<span class="bp-unpin"><svg class="bp-clip" viewBox="0 0 16 16" fill="none" stroke="currentColor" ' +
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="3" width="9" height="11" rx="1.5"/>' +
    '<path d="M6 3V2h4v1M6 7h4M6 10h3"/></svg></span>';
  var FREQ = '<span class="bp-freq">121.955</span>';
  var SEP = '<span class="bp-sep">·</span>';
  var STATES = [
    ["dot", "is-dot", LAMP, "Idle", "Connected, nothing on the radio"],
    ["processing", "s-proc", DOTS + "<span>Processing</span>", "Processing", "Speech or request being processed"],
    ["awaiting", "s-proc is-pulse", LAMP + "<span>Awaiting ATC</span>", "Awaiting ATC", "Request sent"],
    ["atc", "s-atc", BARS + '<span class="bp-who">Ground</span>' + FREQ, "ATC talking", "Controller speaking"],
    ["you", "s-you", BARS + '<span class="bp-who">Transmitting</span>', "Transmitting", "Your readback or request plays"],
    ["ptt", "s-you", MIC + '<span class="bp-who">Transmitting</span>', "PTT held", "Optional: your PTT button"],
    ["readback", "s-atc is-pulse", LAMP + '<span class="bp-who">Awaiting readback</span>' + SEP + "<span>Taxi 12L</span>",
      "Awaiting readback", "ATC waits for your reply"],
    ["insist", "s-insist is-pulse", LAMP + '<span class="bp-who">Awaiting readback ×2</span>', "ATC calls again", "Still no reply"],
    ["negative", "s-insist is-pulse", LAMP + '<span class="bp-who">Negative</span>' + SEP + "<span>QNH 1013</span>",
      "Negative", "ATC corrects your readback"],
    ["ok", "s-ok", CHECK + '<span class="bp-who">Readback OK</span>' + SEP + "<span>Taxi 12L</span>",
      "Readback OK", "ATC took your reply"],
    ["kept", "s-pin", KEPT + "<span>Taxi 12L</span>", "Last clearance", "Optional: kept until the next one"],
    ["missed", "s-insist", LAMP + '<span class="bp-who">No readback</span>' + SEP + "<span>Taxi 12L</span>",
      "No readback", "BeyondATC stopped waiting"],
    ["tune", "s-tune", RADIO + '<span class="bp-who">Tower</span><span class="bp-freq">118.700</span>', "Radio change", "New station on COM1 or COM2"],
    ["contact", "s-tune", RADIO + '<span class="bp-who">Contact</span><span>Approach</span><span class="bp-freq">120.100</span>',
      "Contact", "Auto Tune off: tune this station"],
    ["atis", "s-atis", LAMP + '<span class="bp-who">ATIS</span>' + SEP + "<span>Z</span>", "ATIS change", "New ATIS letter"],
    ["muted", "s-insist is-muted", BARS + '<span class="bp-who">Ground</span>' + FREQ + MUTE, "ATC calls, COM1 muted", "You won't hear it"],
    ["linger", "", LAMP + "<span>Ground</span>" + FREQ, "Exchange ended", "Station for 3 s, then the dot"],
    ["offline", "is-ghost", LAMP + "<span>BATC offline</span>", "Offline", "BeyondATC not running"],
  ];
  function pill(key, unit) {
    for (var i = 0; i < STATES.length; i++) {
      if (STATES[i][0] === key) {
        return '<div id="batc-pill" class="' + STATES[i][1] + '" style="--u:' + unit + 'px"><div class="bp-bg"></div><div class="bp-body">' +
          STATES[i][2] + "</div></div>";
      }
    }
    return "";
  }
  return { STATES: STATES, pill: pill };
})();
