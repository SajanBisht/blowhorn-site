{{- $r := partial "role-data.html" . -}}
{{- partial "cast-page-md.html" (dict "item" $r "getsTitle" (printf "What Blowhorn does for %s" $r.name)) -}}
