{{- $mx := partialCached "action-matrix.html" . "action-matrix" -}}
{{- $copy := $mx.copy -}}
{{- $counts := partial "platform-counts.html" . -}}
# {{ $copy.headline }}

> {{ $copy.lede }}

{{ printf $copy.tally $counts.activities $counts.platforms $counts.comingSoon }}
{{ range $mx.groups }}
## {{ .name }}

{{ .summary }}

| Action |{{ range $mx.platforms }} {{ .name }} |{{ end }}
| --- |{{ range $mx.platforms }} --- |{{ end }}
{{ range .actions }}| {{ .name }} |{{ range .cells }} {{ if .href }}[{{ .statusLabel }}]({{ .href }}){{ else }}{{ .statusLabel }}{{ end }} |{{ end }}
{{ end }}{{ end }}
[{{ $copy.docsCta }}]({{ $copy.docsPath }})
