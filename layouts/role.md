{{- $r := partial "role-data.html" . -}}
# {{ $r.headline }}

> {{ $r.lead }}

## Sound familiar?
{{ range $r.pains }}
- **{{ .t }}.** {{ .b }}
{{- end }}

## What Blowhorn does for {{ $r.name }}
{{ range $r.gets }}
- **{{ .t }}.** {{ .b }}
{{- end }}
{{ with $r.prompt }}
## Or tell your agent

"{{ . }}"
{{ end }}
## Frequently Asked Questions
{{ range $r.faq }}
**{{ .q }}** {{ .a }}
{{ end }}
