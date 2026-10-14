$ErrorActionPreference = "Stop"
$taskRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($args.Count -eq 0) { & python (Join-Path $taskRoot "docker/lotus-core/manage.py") help }
else { & python (Join-Path $taskRoot "docker/lotus-core/manage.py") @args }
exit $LASTEXITCODE
