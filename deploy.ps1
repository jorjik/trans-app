<#
.SYNOPSIS
    Deploy TransApp services to Railway via CLI

.DESCRIPTION
    Deploy individual services (api, bot, miniapp) or all at once to Railway.
    Supports targeting different environments (production, staging, etc.)

.PARAMETER Command
    - all       Deploy all services (default)
    - api       Deploy only the API service
    - bot       Deploy only the Bot service
    - miniapp   Deploy only the Miniapp service
    - status    Show deployment status
    - link      Link local repo to Railway project
    - login     Login to Railway
    - logs      Show logs for a service
    - setup     Create services in Railway project

.PARAMETER ServiceName
    Service name for logs command: api, bot, or miniapp

.PARAMETER Environment
    Target Railway environment (e.g., production, staging)

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -Command api
    .\deploy.ps1 -Command api -Environment production
    .\deploy.ps1 -Command status
    .\deploy.ps1 -Command logs -ServiceName api
    .\deploy.ps1 -Command setup
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet('all', 'api', 'bot', 'miniapp', 'status', 'link', 'login', 'logs', 'setup', 'help')]
    [string]$Command = 'all',

    [Parameter(Position = 1)]
    [string]$ServiceName = '',

    [Alias('e')]
    [string]$Environment = ''
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Info   { Write-Host "[INFO]  $args" -ForegroundColor Cyan }
function Write-Ok     { Write-Host "[OK]    $args" -ForegroundColor Green }
function Write-Warn   { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function Write-Error  { Write-Host "[ERROR] $args" -ForegroundColor Red }

function Get-EnvOpt {
    if ([string]::IsNullOrEmpty($Environment)) {
        return @()
    }
    return @('--environment', $Environment)
}

function Check-Prerequisites {
    $railway = Get-Command railway -ErrorAction SilentlyContinue
    if (-not $railway) {
        Write-Error "Railway CLI is not installed."
        Write-Host "  Install it: npm install -g @railway/cli"
        exit 1
    }

    $null = & railway whoami 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Not logged into Railway. Run: .\deploy.ps1 login"
        exit 1
    }

    $railwayDir = Join-Path $ProjectDir ".railway"
    if (-not (Test-Path $railwayDir)) {
        Write-Error "Project not linked. Run: .\deploy.ps1 link"
        Write-Host ""
        Write-Host "  This opens an interactive prompt to select your Railway project."
        Write-Host "  After linking once, you can deploy without re-linking."
        exit 1
    }
}

function Deploy-Service {
    param([string]$Service)

    $svcDir = Join-Path $ProjectDir $Service

    if (-not (Test-Path $svcDir)) {
        Write-Error "Service directory '$svcDir' not found."
        exit 1
    }

    $envLabel = if ($Environment) { " -> $Environment" } else { "" }
    Write-Info "Deploying '$Service' service$envLabel..."

    Push-Location $svcDir
    try {
        $envOpt = Get-EnvOpt
        & railway up --service $Service @envOpt 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "'$Service' deployed successfully$envLabel!"
        } else {
            Write-Error "Failed to deploy '$Service'."
            exit 1
        }
    } finally {
        Pop-Location
    }
}

function Deploy-All {
    $envLabel = if ($Environment) { " -> $Environment" } else { "" }
    Write-Info "Deploying all services$envLabel..."
    $services = @('api', 'bot', 'miniapp')

    foreach ($svc in $services) {
        Write-Host ""
        Deploy-Service -Service $svc
    }

    Write-Host ""
    Write-Ok "All services deployed!"
}

function Show-Status {
    $envSuffix = if ($Environment) { " ($Environment)" } else { "" }
    Write-Info "Deployment status$envSuffix :"
    $envOpt = Get-EnvOpt
    & railway service status @envOpt 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Could not get status. Is the project linked?"
    }
}

function Show-Logs {
    param([string]$Service)

    if ([string]::IsNullOrEmpty($Service)) {
        Write-Error "Specify a service: .\deploy.ps1 logs -ServiceName api"
        exit 1
    }

    $envOpt = Get-EnvOpt
    & railway logs --service $Service @envOpt
}

function Do-Link {
    Write-Info "Linking project to Railway..."
    & railway link
    $railwayDir = Join-Path $ProjectDir ".railway"
    if (Test-Path $railwayDir) {
        Write-Ok "Project linked!"
    } else {
        Write-Error "Link failed or was cancelled."
        exit 1
    }
}

function Do-Login {
    Write-Info "Opening Railway login..."
    & railway login
}

function Do-Setup {
    Check-Prerequisites
    Write-Info "Setting up services in Railway project..."

    $services = @('api', 'bot', 'miniapp')
    foreach ($svc in $services) {
        Write-Info "Creating service '$svc'..."
        $null = & railway service add $svc 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "Service '$svc' may already exist - skipping."
        }
    }

    Write-Host ""
    Write-Ok "Setup complete! Services created: $($services -join ', ')"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Set environment variables in Railway dashboard or via:"
    foreach ($svc in $services) {
        Write-Host "     railway variables set KEY=VALUE --service $svc"
    }
    Write-Host "  2. Deploy: .\deploy.ps1"
}

function Print-Usage {
    Write-Host "Usage:"
    Write-Host "  .\deploy.ps1                        Deploy all services"
    Write-Host "  .\deploy.ps1 -Command service       Deploy a specific service (api|bot|miniapp)"
    Write-Host "  .\deploy.ps1 -Command status        Show deployment status"
    Write-Host "  .\deploy.ps1 -Command logs -ServiceName svc   Show logs for a service"
    Write-Host "  .\deploy.ps1 -Command link          Link local repo to Railway project"
    Write-Host "  .\deploy.ps1 -Command login         Login to Railway"
    Write-Host "  .\deploy.ps1 -Command setup         Create services in Railway project"
    Write-Host "  .\deploy.ps1 -Command help          Show this help"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Environment env    Target environment (production, staging, etc.)"
    Write-Host "  -e env             Shorthand for -Environment"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy.ps1                              Deploy all to default environment"
    Write-Host "  .\deploy.ps1 -Command api -e production    Deploy only API to production"
    Write-Host "  .\deploy.ps1 -Command all -e staging       Deploy all to staging"
    Write-Host "  .\deploy.ps1 -Command status               Check status"
    Write-Host "  .\deploy.ps1 -Command logs -ServiceName api  View API logs"
}

switch ($Command) {
    'all' {
        Check-Prerequisites
        Deploy-All
    }
    'api' { Check-Prerequisites; Deploy-Service -Service 'api' }
    'bot' { Check-Prerequisites; Deploy-Service -Service 'bot' }
    'miniapp' { Check-Prerequisites; Deploy-Service -Service 'miniapp' }
    'status' { Check-Prerequisites; Show-Status }
    'logs' { Check-Prerequisites; Show-Logs -Service $ServiceName }
    'link' { Do-Link }
    'login' { Do-Login }
    'setup' { Do-Setup }
    'help' { Print-Usage }
    default {
        Write-Error "Unknown command: $Command"
        Print-Usage
        exit 1
    }
}
