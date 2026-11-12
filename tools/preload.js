// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Inlined by tools/build_play.mjs at the top of index.html: starts the downloads of the glb files at once, in the order the game needs them, while the scripts and the asset library are still loading
// (the engine asks for the files only later, one stage after another, and the line was idle between the stages). The responses go to the browser's HTTP cache; the engine's own requests for the same
// URLs then wait for the running download or revalidate (304) and read the cache. Files used only after the page is ready (wrecked cars) start when take37Ready is set.
(function () {
  var LIST = '__LIST__'.split(',');                                     // filled by the build: [now..., '|', after ready...]
  var cut = LIST.indexOf('|'), first = LIST.slice(0, cut), later = LIST.slice(cut + 1), active = 0, queue = first.slice(), MAX = 4;
  if (!window.fetch || /[?&]nopreload=1/.test(location.search)) return;
  function pump() {
    while (active < MAX && queue.length) {
      var u = queue.shift(); active++;
      fetch(u).then(function (r) { return r.ok ? r.arrayBuffer() : null; }).catch(function () {}).then(function () { active--; pump(); });
    }
  }
  pump();
  var t = setInterval(function () { if (window.take37Ready || window.take37Error) { clearInterval(t); queue = later.slice(); MAX = 2; pump(); } }, 500);
})();
