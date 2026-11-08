# Parse into a DOM, validate well-formedness, run an XPath query, re-serialise with formatting.
"$BIN/xmllint" --format "$DATA/catalog.xml" > "$OUT/fmt.xml"
"$BIN/xmllint" --noout --xpath "count(//item[@type='c']/*[local-name()='tags']/tag[.='heap'])" "$DATA/catalog.xml" > "$OUT/xpath.out"
