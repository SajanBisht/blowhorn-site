{{- $item := partial "role-data.html" (dict "page" . "kind" "role") -}}
{{- partial "cast-page-md.html" (dict "item" $item "kind" "role") -}}
