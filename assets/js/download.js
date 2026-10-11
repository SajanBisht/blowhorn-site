// Fills the Download section from the newest published GitHub Release on
// layer5io/blowhorn-site. The newest 100 releases are read first (not
// /releases/latest) so that "no release yet" is an empty list rather than a 404
// that the browser logs as an error. The newest non-draft, non-prerelease
// release is what GitHub's "latest" resolves to, so the always-latest URL and
// this card agree. Only when a full page of 100 holds no stable release (a
// long prerelease train) is /releases/latest asked, where a 404 means none.
//
// States, in order of preference:
//   1. A stable release carries the fixed-name alias (Blowhorn-mac.dmg): one
//      button on the always-latest URL.
//   2. No stable release with the alias yet: the static "on its way" copy stays.
//   3. Any failure (rate limit, outage, offline): say the lookup failed and
//      point at the releases page. Never claim "no build" on an error.
(function () {
  "use strict";

  var card = document.getElementById("download-status");
  if (!card || !window.fetch) {
    return;
  }
  var repo = card.getAttribute("data-repo");
  var alias = card.getAttribute("data-asset");
  var releasesUrl = "https://github.com/" + repo + "/releases";

  function el(tag, text, attrs) {
    var node = document.createElement(tag);
    if (text) {
      node.textContent = text;
    }
    Object.keys(attrs || {}).forEach(function (key) {
      node.setAttribute(key, attrs[key]);
    });
    return node;
  }

  function megabytes(bytes) {
    return Math.max(1, Math.round(bytes / 1048576)) + " MB";
  }

  function publishedOn(iso) {
    var date = new Date(iso);
    if (isNaN(date.getTime())) {
      return null;
    }
    return date.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
  }

  function replaceCard(children) {
    card.textContent = "";
    children.forEach(function (child) {
      card.appendChild(child);
    });
  }

  function showLookupError() {
    var actions = el("p", null, { class: "actions" });
    actions.appendChild(el("a", "See releases", { class: "button button-secondary", href: releasesUrl }));
    replaceCard([
      el("p", "The release check did not go through", { class: "h3" }),
      el("p", "We couldn't load the latest version just now. The releases page always lists the newest build.", { class: "meta" }),
      actions,
    ]);
  }

  function showRelease(release) {
    var assets = Array.isArray(release.assets) ? release.assets : [];
    var version = release.tag_name || release.name || "";
    var aliasAsset = assets.find(function (a) { return a.name === alias; });
    var sums = assets.find(function (a) { return a.name === "SHA256SUMS.txt"; });
    if (!aliasAsset) {
      return;
    }

    var actions = el("p", null, { class: "actions" });
    actions.appendChild(el("a", "Download Blowhorn " + version, {
      class: "button button-primary button-pop",
      href: "https://github.com/" + repo + "/releases/latest/download/" + aliasAsset.name,
    }));
    actions.appendChild(el("span", aliasAsset.name + " · " + megabytes(aliasAsset.size), { class: "caption muted" }));
    var children = [el("p", "Blowhorn " + version + " for Mac", { class: "h3" }), actions];

    var meta = el("p", null, { class: "meta caption" });
    var date = release.published_at ? publishedOn(release.published_at) : null;
    if (date) {
      meta.appendChild(el("span", "Published " + date));
    }
    var notes = el("span");
    notes.appendChild(el("a", "Release notes", { href: release.html_url || releasesUrl }));
    meta.appendChild(notes);
    if (sums) {
      var checksum = el("span");
      checksum.appendChild(el("a", "SHA256SUMS.txt", { href: sums.browser_download_url }));
      meta.appendChild(checksum);
    }
    children.push(meta);
    replaceCard(children);
  }

  var api = "https://api.github.com/repos/" + repo + "/releases";
  var headers = { Accept: "application/vnd.github+json" };

  function latestStable() {
    return fetch(api + "/latest", { headers: headers }).then(function (res) {
      if (res.status === 404) {
        return null;
      }
      if (!res.ok) {
        throw new Error("GitHub answered " + res.status);
      }
      return res.json();
    });
  }

  fetch(api + "?per_page=100", { headers: headers })
    .then(function (res) {
      if (!res.ok) {
        throw new Error("GitHub answered " + res.status);
      }
      return res.json();
    })
    .then(function (releases) {
      if (!Array.isArray(releases)) {
        throw new Error("GitHub answered with something other than a release list");
      }
      var stable = releases.find(function (r) {
        return r && !r.draft && !r.prerelease;
      });
      if (stable) {
        return stable;
      }
      return releases.length === 100 ? latestStable() : null;
    })
    .then(function (stable) {
      if (stable) {
        showRelease(stable);
      }
    })
    .catch(function () {
      showLookupError();
    });
})();
