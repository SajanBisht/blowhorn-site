/* Docs all-actions table (layouts/_partials/action-table.html). Without
   this file the table is plain and every row shows. With it: the filter bar
   appears (text, platform, status), and each sortable column header becomes
   a button that sorts ascending, then descending (aria-sort tells which). */
(function () {
  document.querySelectorAll("[data-action-table]").forEach(function (root) {
    var form = root.querySelector("[data-action-table-filters]");
    var tbody = root.querySelector("tbody");
    var count = root.querySelector("[data-action-table-count]");
    var empty = root.querySelector("[data-action-table-empty]");
    if (!form || !tbody) return;
    var rows = Array.prototype.slice.call(tbody.rows);
    var q = form.querySelector('[data-filter="q"]');
    var platform = form.querySelector('[data-filter="platform"]');
    var status = form.querySelector('[data-filter="status"]');
    var total = rows.length;
    form.hidden = false;
    root.classList.add("is-enhanced");
    rows.forEach(function (row) {
      row.setAttribute("data-text", row.textContent.replace(/\s+/g, " ").toLowerCase());
    });

    function filter() {
      var needle = (q.value || "").trim().toLowerCase();
      var p = platform.value;
      var s = status.value;
      var shown = 0;
      rows.forEach(function (row) {
        var hit = (!p || row.getAttribute("data-platform") === p) &&
          (!s || row.getAttribute("data-status") === s) &&
          (!needle || row.getAttribute("data-text").indexOf(needle) !== -1);
        row.hidden = !hit;
        if (hit) shown += 1;
      });
      if (count) count.textContent = "Showing " + shown + " of " + total;
      if (empty) empty.hidden = shown !== 0;
    }

    var heads = Array.prototype.slice.call(root.querySelectorAll("thead th[data-sort]"));
    function sortBy(key, dir) {
      var numeric = key === "status";
      var sorted = rows.slice().sort(function (a, b) {
        var x = a.getAttribute("data-k-" + key);
        var y = b.getAttribute("data-k-" + key);
        var c = numeric ? Number(x) - Number(y) : x.localeCompare(y);
        if (c === 0) c = Number(a.getAttribute("data-order")) - Number(b.getAttribute("data-order"));
        else if (dir === "descending") c = -c;
        return c;
      });
      sorted.forEach(function (row) { tbody.appendChild(row); });
      heads.forEach(function (th) {
        if (th.getAttribute("data-sort") === key) th.setAttribute("aria-sort", dir);
        else th.removeAttribute("aria-sort");
      });
    }
    heads.forEach(function (th) {
      var key = th.getAttribute("data-sort");
      var button = document.createElement("button");
      button.type = "button";
      button.className = "action-table-sort";
      button.textContent = th.textContent;
      th.textContent = "";
      th.appendChild(button);
      button.addEventListener("click", function () {
        var next = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
        sortBy(key, next);
      });
    });

    q.addEventListener("input", filter);
    platform.addEventListener("change", filter);
    status.addEventListener("change", filter);
    filter();
  });
})();
