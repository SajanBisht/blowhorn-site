---
title: "Where your data lives"
description: "What stays on your Mac, what lives in your organization's store, and what the extension reads."
weight: 281
---

# Where your data lives

Three places hold Blowhorn's data, and each holds a different kind.
Nothing here is a step; for the sharing behind it see
[How Blowhorn works](/docs/explanation/how-it-works/).

On your Mac: the app, the engine checkout, and your Chrome sessions.
Browser sign-ins live in your Chrome profiles, where you made them;
Blowhorn reads them there and copies none of them elsewhere, with one
exception: a Slack workspace session you capture is kept in your
organization's store, below. The daily
logs, the run ledger copy, and the scheduler heartbeat live under the
log directory. The store connection file lives outside the checkout at
mode 0600. A plan attestation, once fetched, is kept in your keychain
for the offline grace.

In your organization's store: the content rows, the schedule, the
profiles, the ledgers, and the run history. The store-credential
platforms keep their secrets there too: GitHub tokens, Hacker News
passwords, and Slack tokens and captured sessions. Every row is scoped
to the organization, and a machine without the organization configured
runs nothing.

On the platforms: whatever Blowhorn published, amplified, or followed
as you, under your name, subject to each destination's own retention.
A published post is the platform's copy; Blowhorn keeps the link and
the outcome, not the content's master.

The extension queries tabs only on the supported sites and reads
cookies there only when the app asks, handing both to the Blowhorn app
on your Mac. The cookies and sign-ins it reads stay on your Mac, with
one exception: today that is your Slack workspace session, which the
app keeps in your organization's store as that profile's Slack
credential. What a run records, such as a new post's link and its
outcome, goes to your organization's store as described above. The extension makes no
requests of its own to any server, sells nothing, and injects no ads.
The [privacy page at blowhorn.ai](https://blowhorn.ai/legal/privacy/) states the same promises; this page
follows it, and the privacy page wins on any difference.

What never belongs in a report, an issue, or a chat message:
credentials, session files, the private connection file, and anything
from your Chrome profile directories. A refusal sentence and an exit
code are enough to diagnose with.

## Related

- [Get help](/docs/reference/support/) - report a problem without secrets.
- [The Blowhorn app, screen by screen](/docs/reference/use-the-desktop-app/) - the log directory listing.
- [Profile reference](/docs/reference/profiles/) - which secrets live where.
- [Chrome extension permissions](/docs/reference/extension-permissions/) - what the extension may read.
