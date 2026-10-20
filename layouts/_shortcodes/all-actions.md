{{- /* Markdown output of all-actions: same rows as the HTML table. */ -}}
{{- $mx := partialCached "action-matrix.html" .Page "action-matrix" }}
| Action | Group | Platform | Status | What it does |
| --- | --- | --- | --- | --- |
{{- range $mx.rows }}
| [{{ .actionName }}]({{ .href | default .platformDocs }}) | {{ .groupName }} | {{ .platformName }} | {{ .statusLabel }} | {{ replace .note "|" "\\|" }}{{ with .limits }} {{ replace . "|" "\\|" }}{{ end }} |
{{- end }}
