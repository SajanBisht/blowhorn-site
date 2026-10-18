# Home page hero variants

The home page hero's headline and subhead come from [`data/hero.json`](../data/hero.json),
which must validate against [`schemas/hero.schema.json`](../schemas/hero.schema.json)
(`make check-schemas`, part of `make site-check` and so of CI). Each variant has an `id`,
a `headline`, a `subhead`, the numbers of the canonical differentiators it rests on
(product repository, `marketing/brand/differentiators.md`) and an optional reviewer `note`.
Copy may only state what those differentiators allow, in their wording rules.

## What ships in the HTML

The variant named by `default` is rendered into the static page by
[`layouts/_partials/hero-variant.html`](../layouts/_partials/hero-variant.html), and the
page's meta, Open Graph, Twitter and JSON-LD descriptions are built from it. Visitors
without JavaScript, crawlers and social previews always get the default. The build fails
if `default` names no variant. `content/en/_index.md`'s `description` is front matter and
does not follow the data file: update it by hand when the default changes.

## Picking a variant at page load

[`assets/js/hero.js`](../assets/js/hero.js) loads synchronously right after the hero
(first party, no network request) and runs an ordered list of selectors. Each selector
gets a context (`variants`, `params`, `referrer`, `language`, `now`) and returns a
variant id or `null`; the first id that names a variant wins.

1. `forced`: `?hero=<id>` shows that variant, for review. Unknown ids are ignored.
2. `daily`: whole UTC days since the epoch, modulo the number of variants, indexes
   `variants` in file order. Every visitor sees the same variant on the same day, and the
   rotation moves on at 00:00 UTC (7:00 PM in Chicago during daylight time).

Only the two text nodes change, so the hero stage animation and its
`prefers-reduced-motion` behaviour are the same for every variant. The chosen id is on
the hero's `data-hero-variant` attribute.

## Adding a selection factor

Write a selector and put it in `selectors` before `daily`, for example:

- **UTM:** `function (c) { return c.params.get('utm_campaign') === 'hn-launch' ? 'own-your-voice' : null; }`
- **Referrer:** match `c.referrer` against a host (`news.ycombinator.com`) and return an id.
- **Locale:** match `c.language` once there are translated variants.
- **Returning visitor:** the site sets no cookies and stores nothing (see the privacy
  page). A returning-visitor rule would need `localStorage`, which the privacy page would
  have to disclose first.

If factors grow beyond a few lines each, move the mapping (for example campaign to id)
into `data/hero.json` and the schema rather than hard-coding ids in the script. No
analytics or third-party script may be added to measure variants (`check-third-party`).

## Review URLs

`https://blowhorn.ai/?hero=<id>` for each id in `data/hero.json`, or the same query on a
local `make site` (`http://localhost:1313/?hero=<id>`).
