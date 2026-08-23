[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$ImageName = "sentinelflow-api:local",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$NodeName = "desktop-control-plane"
)

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "PowerShell 7 or newer is required to preserve the binary image stream."
}

docker image inspect $ImageName | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Docker image '$ImageName' does not exist. Build it before importing."
}

docker container inspect $NodeName | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Kubernetes node container '$NodeName' does not exist."
}

docker image save $ImageName | docker exec -i $NodeName ctr -n k8s.io images import -
if ($LASTEXITCODE -ne 0) {
    throw "Failed to import '$ImageName' into '$NodeName'."
}

Write-Output "Imported '$ImageName' into Kubernetes node '$NodeName'."
