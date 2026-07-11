param(
    [string]$MinikubeProfile = "minikube",
    [int]$MinikubeCpus = 4,
    [int]$MinikubeMemoryMb = 7168,
    [switch]$OpenUiTunnels = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
    & $Command
}

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$CommandName)
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Commande manquante: '$CommandName'. Installe-la puis relance le script."
    }
}

function Wait-NodeMetrics {
    param(
        [int]$MaxAttempts = 12,
        [int]$DelaySeconds = 5
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        # "kubectl top" from host can fail with client/server version mismatch.
        # Use "minikube kubectl" to run the version bundled with the cluster.
        # Keep retrying without stopping the whole script on transient errors.
        $previousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & minikube kubectl -- top nodes 1>$null 2>$null
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }

        if ($LASTEXITCODE -eq 0) {
            return
        }

        Write-Host "Metrics API pas encore disponible (tentative $attempt/$MaxAttempts)..." -ForegroundColor Yellow
        Start-Sleep -Seconds $DelaySeconds
    }

    throw "minikube kubectl -- top nodes indisponible apres plusieurs tentatives."
}

function Start-UiTunnelTerminal {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ServiceName,
        [Parameter(Mandatory = $true)]
        [string]$ProfileName,
        [string]$UrlSuffix = ""
    )

    if ([string]::IsNullOrWhiteSpace($UrlSuffix)) {
        $command = "minikube service $ServiceName -n backtobasics --url -p $ProfileName"
    }
    else {
        $commandTemplate = @'
minikube service __SERVICE__ -n backtobasics --url -p __PROFILE__ | ForEach-Object {
    if ($_ -match '^http') {
        Write-Output ($_.TrimEnd('/') + '__SUFFIX__')
    }
    else {
        Write-Output $_
    }
}
'@
        $command = $commandTemplate
        $command = $command.Replace("__SERVICE__", $ServiceName)
        $command = $command.Replace("__PROFILE__", $ProfileName)
        $command = $command.Replace("__SUFFIX__", $UrlSuffix)
    }

    Start-Process -FilePath "powershell" -ArgumentList @("-NoExit", "-Command", $command) | Out-Null
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$secretFile = Join-Path $repoRoot "k8s\secrets\minio.yaml"

Push-Location $repoRoot
try {
    Test-CommandExists -CommandName "minikube"
    Test-CommandExists -CommandName "kubectl"
    Test-CommandExists -CommandName "docker"

    $isRunning = $false
    $statusJson = & minikube status -p $MinikubeProfile --output=json 2>$null
    if ($LASTEXITCODE -eq 0 -and $statusJson) {
        $status = $statusJson | ConvertFrom-Json
        $isRunning = (
            $status.Host -eq "Running" -and
            $status.Kubelet -eq "Running" -and
            $status.APIServer -eq "Running"
        )
    }

    if ($isRunning) {
        Write-Host "Minikube profile '$MinikubeProfile' est deja demarre : start ignore." -ForegroundColor Yellow
    }
    else {
        Invoke-Step -Message "Demarrage Minikube ($MinikubeCpus CPU / $MinikubeMemoryMb MB)" -Command {
            minikube start -p $MinikubeProfile --cpus=$MinikubeCpus --memory=$MinikubeMemoryMb
        }
    }

    Invoke-Step -Message "Selection du contexte kubectl du profile" -Command {
        minikube -p $MinikubeProfile update-context
    }

    Invoke-Step -Message "Verification des noeuds Kubernetes" -Command {
        kubectl get nodes
    }

    Invoke-Step -Message "Activation metrics-server (HPA / kubectl top)" -Command {
        minikube addons enable metrics-server
    }

    Invoke-Step -Message "Attente de disponibilite des metriques noeuds" -Command {
        Wait-NodeMetrics
    }

    Invoke-Step -Message "Verification des metriques noeuds" -Command {
        minikube kubectl -- top nodes
    }

    Invoke-Step -Message "Connexion au daemon Docker de Minikube" -Command {
        $dockerEnvLines = minikube -p $MinikubeProfile docker-env --shell powershell
        $dockerEnvScript = $dockerEnvLines -join [Environment]::NewLine
        Invoke-Expression $dockerEnvScript
    }

    Invoke-Step -Message "Build image backtobasics:latest" -Command {
        docker build -t backtobasics:latest .
    }

    if (-not (Test-Path -Path $secretFile)) {
        $exampleFile = Join-Path $repoRoot "k8s\secrets\minio.yaml.example"
        if (Test-Path -Path $exampleFile) {
            Write-Host "Secret absent: copie depuis minio.yaml.example" -ForegroundColor Yellow
            Copy-Item -Path $exampleFile -Destination $secretFile
        }
        else {
            throw "Secret introuvable: '$secretFile'. Cree ce fichier local avant de deployer."
        }
    }

    $applyOrder = @(
        "k8s/namespace.yaml",
        "k8s/configmaps/",
        "k8s/secrets/minio.yaml",
        "k8s/redis/",
        "k8s/minio/",
        "k8s/api/",
        "k8s/worker/",
        "k8s/kube-state-metrics/",
        "k8s/flower/",
        "k8s/prometheus/",
        "k8s/grafana/"
    )

    foreach ($target in $applyOrder) {
        Invoke-Step -Message "kubectl apply -f $target" -Command {
            kubectl apply -f $target
        }
    }

    $rollouts = @(
        "deployment/api",
        "deployment/worker",
        "deployment/kube-state-metrics",
        "deployment/prometheus",
        "deployment/grafana"
    )

    foreach ($rollout in $rollouts) {
        Invoke-Step -Message "Attente rollout $rollout" -Command {
            kubectl -n backtobasics rollout status $rollout
        }
    }

    $minikubeIp = (minikube ip -p $MinikubeProfile).Trim()
    Write-Host ""
    Write-Host "Stack K8s deployee." -ForegroundColor Green
    Write-Host "API (docs) : http://$minikubeIp`:30500/docs"
    Write-Host "Flower     : http://$minikubeIp`:30555"
    Write-Host "Prometheus : http://$minikubeIp`:30900"
    Write-Host "Grafana    : http://$minikubeIp`:30300"
    Write-Host "MinIO UI   : via terminal tunnel (service minio, port console 9001)"

    if ($OpenUiTunnels) {
        Write-Host ""
        Write-Host "Ouverture des tunnels UI (api, flower, grafana, minio)..." -ForegroundColor Cyan
        Start-UiTunnelTerminal -ServiceName "api" -ProfileName $MinikubeProfile -UrlSuffix "/docs"
        Start-UiTunnelTerminal -ServiceName "flower" -ProfileName $MinikubeProfile
        Start-UiTunnelTerminal -ServiceName "grafana" -ProfileName $MinikubeProfile
        Start-UiTunnelTerminal -ServiceName "minio" -ProfileName $MinikubeProfile
        Write-Host "Quatre terminaux ont ete lances. Garde-les ouverts pendant la demo." -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
