# Home page hero variants

The home page hero's headline, subhead and illustration come from [`data/hero.json`](../data/hero.json),
which must validate against [`schemas/hero.schema.json`](../schemas/hero.schema.json)
(`make check-schemas`, part of `make site-check` and so of CI). Each variant has an `id`,
a `headline`, a `subhead`, an optional `art` (`stage` or `fan`, default `stage`), the
numbers of the canonical differentiators it rests on and an optional reviewer `note`.
Copy may only state what those differentiators allow, in their wording rules.

## The rotation

`rotation` is the config object. `rotation.mode` is `utc-day` (production) or
`interval`. `rotation.ids` lists the heroes that take turns, in order. Omit `ids`
to rotate every variant. Variants not listed stay in the file for later.

Production rotates these five, one per UTC day:

1. `not-a-bot`: "Not a bot. You, at full volume." over the hero stage, Major Blowhorn
   barking into your own Chrome while the post types itself. Default and fallback.
2. `real-you`: "The real you, everywhere at once."
3. `your-fleet`: "Your fleet. Your Chrome. Your voice."
4. `sound-wave`: "Real voices make a sound wave."
5. `own-your-voice`: "Own your voice. Keep your accounts."

The platforms section headline lives in `data/integrations.json` (`headline`).
It is not a hero. The old line "Say it once. Say it everywhere." stays on the
Reveille homepage only.

At page load each visitor gets one of

```
rotation.ids[floor(UTC days since the epoch) % length]   # mode: utc-day
rotation.ids[floor(now / intervalSeconds) % length]      # mode: interval
```

`utc-day` is whole UTC days since the Unix epoch, so every visitor sees the same
hero on the same day and the turn happens at 00:00 UTC. `interval` needs
`rotation.intervalSeconds` (a positive integer). The pick happens once: the hero
never changes while someone is reading the page.

## How it renders

- [`layouts/_partials/hero-rotation.html`](../layouts/_partials/hero-rotation.html) reads
  the data file and fails the build if `rotation.ids` names an unknown variant
  or if `default` is not in the rotating ids. Mode and `intervalSeconds` are
  schema-checked (`make check-schemas`).
- [`layouts/home.html`](../layouts/home.html) renders the hero once: one `h1` and one
  subhead holding a `<span data-hero-only="<id>">` per rotating hero, the shared label,
  buttons and social proof, and one figure per art used by the rotation, each from its own
  partial in [`layouts/_partials/hero-art/`](../layouts/_partials/hero-art/).
- [`layouts/_partials/hero-rotation-head.html`](../layouts/_partials/hero-rotation-head.html),
  in the page's `head`, carries a few lines of CSS that hide every span and figure except
  the picked one, and a few lines of inline script that pick the hero and set
  `data-hero` and `data-hero-art` on `<html>`. It runs before the body is parsed, so the
  first paint already shows the right hero: no flash and no layout shift.
- Hidden copy and art are `display: none`, so screen readers get only the visible hero
  and the page has one `h1`.
- Without JavaScript the attributes are never set and the CSS shows `default`.
  `default` also feeds the meta, Open Graph, Twitter and JSON-LD descriptions
  ([`layouts/_partials/hero-variant.html`](../layouts/_partials/hero-variant.html)), so
  crawlers and social previews always get it. `content/en/_index.md`'s `description` is
  front matter and does not follow the data file: update it by hand when the default
  changes.
- While the fan is the hero, the Platforms section hides its own copy of the fan
  (`.platforms-fan` in `assets/css/site.css`), so it never appears twice.
- Each art keeps its own motion and `prefers-reduced-motion` rules. Switching heroes adds
  no transition.

## Adding a hero

1. Add the variant to `variants` (with `art` if it is not the stage).
2. Add its id to `rotation.ids`.
3. For a new illustration, add `layouts/_partials/hero-art/<art>.html` (a `figure` with
   `class="hero-art"` and `data-hero-art-only="<art>"`, every id in it unique on the
   page) and add `<art>` to the `art` enum in the schema.

## Review URLs

`?hero=<n>` (1-based position in `rotation.ids`) or `?hero=<id>` (any id in
`rotation.ids`) forces a hero, for example `https://blowhorn.ai/?hero=2` or
`http://localhost:1313/?hero=real-you` on a local `make site`. Anything else is
ignored and the time rule applies.

No analytics or third-party script may be added to measure heroes (`check-third-party`).
