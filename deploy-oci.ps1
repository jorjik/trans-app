<#
.SYNOPSIS
    Deploy TransApp to Oracle Cloud Infrastructure (OCI) Compute VM

.DESCRIPTION
    Syncs project files to OCI VM via rsync/ssh, then runs docker compose up.
    Requires an existing OCI Compute VM with Docker + Compose installed.

.PARAMETER Host
    OCI VM public IP or hostname (required)

.PARAMETER User
    SSH user (default: ubuntu)

.PARAMETER KeyPath
    Path to SSH private key (default: ~/.ssh/id_rsa)

.PARAMETER SkipBuild
    Skip docker compose build (use existing images)

.PARAMETER Restart
    Force restart of all containers (docker compose up --force-recreate)

.PARAMETER Logs
    Show logs after deployment

.PARAMETER DryRun
    Show what would be done without actually doing it

.EXAMPLE
    .\deploy-oci.ps1 -Host 129.151.100.50
    .\deploy-oci.ps1 -Host 129.151.100.50 -KeyPath ~\.ssh\oci_key
    .\deploy-oci.ps1 -Host my-vm.example.com --Logs
    .\deploy-oci.ps1 -Host 129.151.100.50 -SkipBuild
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [Alias('h')]
    [string]$HostAddress,

    [Parameter()]
    [Alias('u')]
    [string]$User = 'ubuntu',

    [Parameter()]
    [Alias('k')]
    [string]$KeyPath = "$env:USERPROFILE\.ssh\id_rsa",

    [Parameter()]
    [switch]$SkipBuild,

    [Parameter()]
    [Alias('r')]
    [switch]$Restart,

    [Parameter()]
    [Alias('l')]
    [switch]$Logs,

    [Parameter()]
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Info   { Write-Host "[INFO]  $args" -ForegroundColor Cyan }
function Write-Ok     { Write-Host "[OK]    $args" -ForegroundColor Green }
function Write-Warn   { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function Write-Error  { Write-Host "[ERROR] $args" -ForegroundColor Red }

# ── Checks ──────────────────────────────────────────────────────────────

if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Error "SSH client not found. Install OpenSSH Client."
    exit 1
}

if (-not (Get-Command rsync -ErrorAction SilentlyContinue)) {
    Write-Error "rsync not found. Install it: winget install rsync"
    Write-Info "Or use WSL: wsl rsync ..."
    exit 1
}

if (-not (Test-Path $KeyPath)) {
    Write-Warn "SSH key not found at: $KeyPath"
    $KeyPath = Read-Host "Enter path to SSH private key (or leave empty to use password auth)"
}

$sshBase = @('ssh')
if ($KeyPath) { $sshBase += '-i', $KeyPath }
$sshBase += '-o', 'StrictHostKeyChecking=accept-new'
$sshBase += '-o', 'ConnectTimeout=10'

$sshTarget = "$User@$HostAddress"
$remoteAppDir = '/opt/trans-app'
$composeFile = 'docker-compose.prod.yml'

function Invoke-Ssh {
    param([string]$Command, [string]$Description)
    Write-Info $Description
    if ($DryRun) {
        Write-Host "  [DRY-RUN] ssh $sshTarget $Command"
        return ''
    }
    $output = & ssh $sshBase $sshTarget $Command 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "SSH command failed: $output"
        exit 1
    }
    $output | ForEach-Object { Write-Host "  $_" }
    return $output
}

function Invoke-Rsync {
    param([string]$Source, [string]$Dest, [string]$Description)
    Write-Info $Description
    if ($DryRun) {
        Write-Host "  [DRY-RUN] rsync $Source $sshTarget`:$Dest"
        return
    }
    $rsyncArgs = @(
        '-avz', '--delete',
        '--exclude', '.git',
        '--exclude', 'node_modules',
        '--exclude', '__pycache__',
        '--exclude', '*.pyc',
        '--exclude', 'venv',
        '--exclude', '.venv',
        '--exclude', '.env',
        '--exclude', '*.session',
        '--exclude', 'dist',
        '--exclude', 'dist-ssr',
        '--exclude', '.vscode',
        '--exclude', '.idea',
        '--exclude', '*.tsbuildinfo',
        '-e', "ssh $(if ($KeyPath) { "-i $KeyPath" } else { "" }) -o StrictHostKeyChecking=accept-new"
    )
    & rsync $rsyncArgs $Source "$sshTarget`:$Dest"
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Files synced to $Dest"
    } else {
        Write-Error "rsync failed with exit code $LASTEXITCODE"
        exit 1
    }
}

# ── Pre-flight check ───────────────────────────────────────────────────

Write-Info "Checking connection to $HostAddress ..."
$hostCheck = & ssh $sshBase "$User@$HostAddress" 'echo OK' 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Cannot SSH to $HostAddress. Check IP, key, and network."
    Write-Host $hostCheck
    exit 1
}
Write-Ok "SSH connection OK"

# ── Step 1: Ensure remote directory exists ──────────────────────────────

Invoke-Ssh -Command "sudo mkdir -p $remoteAppDir && sudo chown -R `$USER:`$USER $remoteAppDir" `
    -Description "Creating remote app directory: $remoteAppDir"

# ── Step 2: Sync project files ──────────────────────────────────────────

Write-Host ""
Invoke-Rsync -Source "$ProjectDir/" -Dest "$remoteAppDir/" `
    -Description "Syncing project files to $HostAddress ..."

# ── Step 3: Upload .env file (separately, not blanket-synced) ───────────

$envFile = Join-Path $ProjectDir '.env'
if (Test-Path $envFile) {
    Write-Host ""
    Write-Info "Uploading .env file ..."
    if (-not $DryRun) {
        & scp @(
            if ($KeyPath) { '-i', $KeyPath } else { '' }
            '-o', 'StrictHostKeyChecking=accept-new'
            $envFile, "$sshTarget`:$remoteAppDir/.env"
        ) 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok ".env uploaded"
        } else {
            Write-Warn "Failed to upload .env — you may need to create it manually on the VM"
        }
    } else {
        Write-Host "  [DRY-RUN] scp $envFile → $remoteAppDir/.env"
    }
} else {
    Write-Warn ".env not found locally. Create it on the remote VM:"
    Write-Warn "  ssh $sshTarget 'nano $remoteAppDir/.env'"
}

# ── Step 4: Docker Compose deploy ───────────────────────────────────────

Write-Host ""
$buildFlag = if ($SkipBuild) { '' } else { '--build' }
$recreateFlag = if ($Restart) { '--force-recreate' } else { '' }

Invoke-Ssh -Command "cd $remoteAppDir && docker compose -f $composeFile up -d $buildFlag $recreateFlag --remove-orphans" `
    -Description "Starting containers with Docker Compose ..."

# ── Step 5: Show status ─────────────────────────────────────────────────

Write-Host ""
Invoke-Ssh -Command "cd $remoteAppDir && docker compose -f $composeFile ps" `
    -Description "Container status"

# ── Step 6: Logs (optional) ─────────────────────────────────────────────

if ($Logs) {
    Write-Host ""
    Invoke-Ssh -Command "cd $remoteAppDir && docker compose -f $composeFile logs --tail=50" `
        -Description "Recent logs"
}

# ── Done ────────────────────────────────────────────────────────────────

Write-Host ""
Write-Ok "Deployment complete!"
Write-Host ""
Write-Host "Health checks:" -ForegroundColor Cyan
Write-Host "  API:       curl http://$HostAddress`:8000/health"
Write-Host "  Mini App:  curl http://$HostAddress`:3000"
Write-Host "  SSH:        ssh $(if ($KeyPath) { "-i $KeyPath " })${User}@${HostAddress}"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Set up OCI Security List to allow ports 8000, 3000"
Write-Host "  2. Configure Telegram webhook:"
Write-Host "     curl https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://$HostAddress`:$PORT/webhook"
Write-Host "  3. (Recommended) Set up Nginx + Let's Encrypt for HTTPS"
