// Home page hero variants (#hero-title and its subhead). The static HTML already
// carries the default variant from data/hero.json, so visitors without JavaScript,
// crawlers and social previews all get it. This script may swap in another variant
// before first paint: it loads synchronously right after the hero and only replaces
// two text nodes, so the hero stage animation runs the same for every variant.
//
// Selection is an ordered list of selectors. Each one gets the context and returns
// a variant id or null; the first known id wins. To add a factor (referrer, UTM,
// locale, returning visitor), add a selector to the list above `daily`.
// See docs/hero-variants.md.
(function () {
  var hero = document.querySelector('[data-hero-variant]');
  var data = document.getElementById('hero-variants');
  if (!hero || !data) return;
  var config;
  try { config = JSON.parse(data.textContent); } catch (e) { return; }
  var variants = config.variants || [];
  if (!variants.length) return;
  var byId = {};
  variants.forEach(function (v) { byId[v.id] = v; });

  var ctx = {
    variants: variants,
    params: new URLSearchParams(window.location.search),
    referrer: document.referrer,
    language: navigator.language || '',
    now: new Date()
  };

  // ?hero=<id> forces a variant, for review.
  function forced(c) { return c.params.get('hero'); }

  // Deterministic rotation: whole UTC days since the epoch, modulo the number of
  // variants, so every visitor sees the same variant on the same day.
  function daily(c) {
    var day = Math.floor(c.now.getTime() / 86400000);
    return c.variants[day % c.variants.length].id;
  }

  var selectors = [forced, daily];
  var pick = null;
  for (var i = 0; i < selectors.length && !pick; i++) {
    var id = selectors[i](ctx);
    if (id && byId[id]) pick = byId[id];
  }
  if (!pick || pick.id === hero.getAttribute('data-hero-variant')) return;

  var title = hero.querySelector('#hero-title');
  var sub = hero.querySelector('.hero-sub');
  if (title) title.textContent = pick.headline;
  if (sub) sub.textContent = pick.subhead;
  hero.setAttribute('data-hero-variant', pick.id);
})();
