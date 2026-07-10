$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $root "logs"
if (!(Test-Path $logDir)) {
  New-Item -ItemType Directory -Path $logDir | Out-Null
}

$outLog = Join-Path $logDir "uvicorn.out.log"
$errLog = Join-Path $logDir "uvicorn.err.log"

Start-Process `
  -FilePath (Join-Path $root ".venv\\Scripts\\python.exe") `
  -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $outLog `
  -RedirectStandardError $errLog `
  -WindowStyle Hidden
