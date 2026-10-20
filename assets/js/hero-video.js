// The Signal hero film (layouts/_partials/hero-video.html, data/hero.json
// media.video). Autoplay needs muted, so the film starts muted and looping
// once the hero is on screen, with a Sound on toggle and a Pause toggle
// (motion over five seconds needs a pause). It pauses off screen and resumes
// on return unless the visitor paused it. Under prefers-reduced-motion it
// waits on its poster behind a Play button; a click plays it with sound.
// No JavaScript: the native controls stay.
(function () {
  var fig = document.querySelector('[data-hero-film]');
  if (!fig || fig.offsetParent === null) return;
  var video = fig.querySelector('video');
  var start = fig.querySelector('[data-film="start"]');
  var bar = fig.querySelector('[data-film="bar"]');
  var sound = fig.querySelector('[data-film="sound"]');
  var soundLabel = fig.querySelector('[data-film="sound-label"]');
  var pause = fig.querySelector('[data-film="pause"]');
  var pauseLabel = fig.querySelector('[data-film="pause-label"]');
  var reduce = false;
  try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  var held = false, visible = true;

  video.removeAttribute('controls');
  video.muted = true;

  function sync() {
    sound.setAttribute('aria-pressed', String(!video.muted));
    soundLabel.textContent = video.muted ? 'Sound on' : 'Sound off';
    fig.classList.toggle('is-sound', !video.muted);
    pause.setAttribute('aria-pressed', String(video.paused));
    pauseLabel.textContent = video.paused ? 'Play' : 'Pause';
    fig.classList.toggle('is-paused', video.paused);
  }
  function play() {
    var p = video.play();
    if (p && p.catch) p.catch(function () { held = true; showStart(); });
  }
  function showStart() { start.hidden = false; bar.hidden = true; }
  function begin(withSound) {
    start.hidden = true;
    bar.hidden = false;
    if (withSound) video.muted = false;
    held = false;
    play();
  }

  start.addEventListener('click', function () { begin(true); });
  sound.addEventListener('click', function () {
    video.muted = !video.muted;
    if (!video.muted && video.paused) { held = false; play(); }
    sync();
  });
  pause.addEventListener('click', function () {
    if (video.paused) { held = false; play(); } else { held = true; video.pause(); }
    sync();
  });
  ['play', 'pause', 'volumechange'].forEach(function (ev) { video.addEventListener(ev, sync); });

  if (reduce) { showStart(); return; }
  bar.hidden = false;
  sync();
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      visible = es[0].isIntersecting;
      if (!visible && !video.paused) video.pause();
      else if (visible && !held && video.paused) play();
    }, { threshold: 0.25 }).observe(fig);
  } else {
    play();
  }
})();
