// The Signal hero film (layouts/_partials/hero-video.html). Its data-*
// attributes come from data/hero.json media.video.playback:
//   autoplay  true: play muted once on screen (browsers only autoplay muted).
//             false: wait on the poster behind a Play button.
//   loop      replay from the start when it ends.
//   sound     the Play button starts it with sound (a click is a user
//             gesture, so browsers allow audio).
//   end       poster or last-frame when it ends without loop; a Watch again
//             button shows either way.
// Under prefers-reduced-motion it never autoplays. While playing, Sound and
// Pause toggles show; it pauses off screen and resumes on return unless the
// visitor paused it. Without JavaScript the native controls stay.
(function () {
  var fig = document.querySelector('[data-hero-film]');
  if (!fig || fig.offsetParent === null) return;
  var video = fig.querySelector('video');
  var q = function (n) { return fig.querySelector('[data-film="' + n + '"]'); };
  var start = q('start'), startLabel = q('start-label'), bar = q('bar');
  var sound = q('sound'), soundLabel = q('sound-label');
  var pause = q('pause'), pauseLabel = q('pause-label');
  var cfg = fig.dataset;
  var reduce = false;
  try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  var autoplay = cfg.autoplay === 'true' && !reduce;
  var withSound = cfg.sound === 'true';
  var started = false, held = false;

  video.removeAttribute('controls');
  video.loop = cfg.loop === 'true';
  video.muted = autoplay || !withSound;

  function sync() {
    sound.setAttribute('aria-pressed', String(!video.muted));
    soundLabel.textContent = video.muted ? 'Sound on' : 'Sound off';
    fig.classList.toggle('is-sound', !video.muted);
    pause.setAttribute('aria-pressed', String(video.paused));
    pauseLabel.textContent = video.paused ? 'Play' : 'Pause';
    fig.classList.toggle('is-paused', video.paused);
  }
  function showStart(label) {
    startLabel.textContent = label;
    start.hidden = false;
    bar.hidden = true;
    fig.classList.add('is-waiting');
  }
  function play() {
    var p = video.play();
    if (p && p.catch) p.catch(function () { started = false; showStart('Play the film'); });
  }
  function begin(userGesture) {
    started = true;
    held = false;
    start.hidden = true;
    bar.hidden = false;
    fig.classList.remove('is-waiting');
    if (userGesture && withSound) video.muted = false;
    play();
    sync();
  }

  start.addEventListener('click', function () {
    if (video.ended || video.currentTime >= video.duration) video.currentTime = 0;
    begin(true);
  });
  sound.addEventListener('click', function () {
    video.muted = !video.muted;
    sync();
  });
  pause.addEventListener('click', function () {
    if (video.paused) { held = false; play(); } else { held = true; video.pause(); }
    sync();
  });
  video.addEventListener('ended', function () {
    if (video.loop) return;
    started = false;
    if (cfg.end === 'poster') video.load();
    showStart('Watch again');
  });
  ['play', 'pause', 'volumechange'].forEach(function (ev) { video.addEventListener(ev, sync); });

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      var visible = es[0].isIntersecting;
      if (!visible && !video.paused) video.pause();
      else if (visible && video.paused && !held && (started || (autoplay && !video.ended))) {
        if (!started) begin(false); else play();
      }
    }, { threshold: 0.25 }).observe(fig);
  } else if (autoplay) {
    begin(false);
  }
  if (!autoplay) showStart('Play the film');
})();
