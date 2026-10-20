{{- $item := partial "role-data.html" (dict "page" . "kind" "use-case") -}}
{{- partial "cast-page-md.html" (dict "item" $item "kind" "use-case") -}}
