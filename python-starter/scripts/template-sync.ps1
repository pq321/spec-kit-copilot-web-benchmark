param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("bootstrap", "sync")]
    [string]$Mode,

    [string]$Workspace = (Get-Location).Path,
    [string]$SourceUri = "https://github.com/pq321/spec-kit-copilot-web-benchmark/archive/refs/heads/main.zip",
    [string]$SourceZipPath,
    [string]$RemoteSubdir = "python-starter",
    [string]$ArchiveRootPrefix = "spec-kit-copilot-web-benchmark-main",
    [string]$StateDirName = ".template-sync",
    [switch]$Json
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptRoot
$srcPath = Join-Path $repoRoot "src"

if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$srcPath;$($env:PYTHONPATH)"
} else {
    $env:PYTHONPATH = $srcPath
}

$pythonCandidates = @("python", "py")
$pythonCommand = $null
foreach ($candidate in $pythonCandidates) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($command) {
        $pythonCommand = $candidate
        break
    }
}

if (-not $pythonCommand) {
    throw "Python is required for template sync. Install Python or activate the project conda environment first."
}

$args = @(
    "-m", "template_sync.cli",
    $Mode,
    "--workspace", $Workspace,
    "--source-uri", $SourceUri,
    "--remote-subdir", $RemoteSubdir,
    "--archive-root-prefix", $ArchiveRootPrefix,
    "--state-dir-name", $StateDirName
)

if ($SourceZipPath) {
    $args += @("--source-zip-path", $SourceZipPath)
}

if ($Json) {
    $args += "--json"
}

& $pythonCommand @args
exit $LASTEXITCODE
