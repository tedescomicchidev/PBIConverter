# Mapping Catalogue

This document enumerates key Tableau-to-DAX translations implemented by the migrator.

| Tableau Pattern | DAX Output | Notes |
| --- | --- | --- |
| `[Profit]/[Sales]` | `DIVIDE([Profit], [Sales])` | Uses DIVIDE to prevent divide-by-zero errors. |
| `IF <condition> THEN <a> ELSE <b>` | `IF(<condition>, <a>, <b>)` | Nested branches convert to `SWITCH(TRUE(), ...)` when needed. |
| `{ FIXED [Region]: SUM([Sales]) }` | `CALCULATE(SUM(Fact[Sales]), ALLEXCEPT(DimRegion, DimRegion[Region]))` | Applies filters to maintain Region grain. |
| `{ INCLUDE [Subcategory]: SUM([Sales]) }` | `SUMX(VALUES(DimSubcategory[Subcategory]), [Sales])` | Iterates over included dimension members. |
| `{ EXCLUDE [Region]: SUM([Sales]) }` | `CALCULATE([Sales], REMOVEFILTERS(DimRegion[Region]))` | Removes region filters while respecting other contexts. |
| `RUNNING_SUM(SUM([Sales]))` | `CALCULATE(SUM(Fact[Sales]), FILTER(ALLSELECTED('Date'[Date]), 'Date'[Date] <= MAX('Date'[Date])))` | Requires explicit ordering over canonical date. |
| `WINDOW_SUM(SUM([Sales]))` | `CALCULATE(SUM(Fact[Sales]), FILTER(ALLSELECTED('Date'), <window>))` | Emits TODO due to unspecified ordering. |

Unsupported or ambiguous functions emit actionable TODOs in the generated DAX and are listed in the migration report.
