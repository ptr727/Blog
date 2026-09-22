---
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
date: '{{ .Date }}'
url: /{{ replaceRE "^posts/" "" .File.Dir }}{{ .File.ContentBaseName }}/
categories:
- uncategorized
tags:
- replace-me
---
