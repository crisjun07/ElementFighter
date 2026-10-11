/* ═══════════════════════════════════════════════════════════════
   game.js  —  Entry point
   All <script> tags are at bottom of <body>, so DOM + all prior
   scripts are fully executed before this file runs.
════════════════════════════════════════════════════════════════ */

// Unlock AudioContext on first user gesture (required by browsers)
document.addEventListener('click',      function() { if (typeof AudioManager !== 'undefined') AudioManager.ensureCtx(); }, { once: true });
document.addEventListener('touchstart', function() { if (typeof AudioManager !== 'undefined') AudioManager.ensureCtx(); }, { once: true });
document.addEventListener('keydown',    function() { if (typeof AudioManager !== 'undefined') AudioManager.ensureCtx(); }, { once: true });

// Boot — wrapped in try/catch so any crash shows a useful message
try {
  UIManager.boot();
} catch (e) {
  console.error('[Element Fighter] Boot error:', e);
  document.body.innerHTML =
    '<div style="color:#ff4444;font-family:monospace;padding:32px;background:#050a14;min-height:100vh;">' +
    '<h2>&#9888; Element Fighter failed to start</h2>' +
    '<p>' + e.message + '</p>' +
    '<pre style="font-size:.8rem;color:#ff8888;white-space:pre-wrap;">' + e.stack + '</pre>' +
    '</div>';
}
