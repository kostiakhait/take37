# Sets BelowNormal on the given process id and on the Playwright browser processes (their command line names ms-playwright); prints what it changed.
param([int]$procId = 0)
$n = 0
if ($procId -gt 0) { try { (Get-Process -Id $procId).PriorityClass = 'BelowNormal'; $n++ } catch {} }
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*ms-playwright*' } | ForEach-Object { try { (Get-Process -Id $_.ProcessId).PriorityClass = 'BelowNormal'; $n++ } catch {} }
"BelowNormal: $n processes"
