# {{ .Title }}

> {{ .Params.lead }}
{{ range .Pages.ByWeight }}{{ $r := partial "role-data.html" . }}
- [For {{ $r.name }}: {{ $r.headline }}]({{ .Permalink }})
{{- end }}
