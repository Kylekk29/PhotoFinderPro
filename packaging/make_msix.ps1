<#
.SYNOPSIS  Build the Microsoft Store MSIX from dist\PhotoFinderPro\ (run packaging\build.bat first).
.PARAMETER TestSign  Also create dist\PhotoFinderPro-<ver>-testsigned.msix, signed with a self-signed cert
                     in CurrentUser\My (local testing only; never upload that file to the Store).
Identity (name / publisher / publisher display name / version) comes from packaging\msix\store_identity.json.
Output: dist\PhotoFinderPro-<major.minor.patch>.msix  (unsigned; the Store signs it).
#>
param([switch]$TestSign)
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$msixSrc = Join-Path $PSScriptRoot 'msix'
$dist = Join-Path $root 'dist'
$app = Join-Path $dist 'PhotoFinderPro'
$stage = Join-Path $root 'build\msix'

if (-not (Test-Path (Join-Path $app 'PhotoFinderPro.exe'))) { throw "dist\PhotoFinderPro\PhotoFinderPro.exe not found. Run packaging\build.bat first." }

# --- tools: Windows SDK if present, else tools\sdk-buildtools (NuGet Microsoft.Windows.SDK.BuildTools)
function Find-Tool($name) {
    $c = @()
    foreach ($b in @("${env:ProgramFiles(x86)}\Windows Kits\10\bin", (Join-Path $root 'tools\sdk-buildtools\pkg\bin'))) {
        if (Test-Path $b) { $c += Get-ChildItem $b -Recurse -Filter $name -ErrorAction SilentlyContinue | Where-Object { $_.FullName -like '*\x64\*' } }
    }
    if (-not $c) { throw "$name not found. Install the Windows SDK or extract NuGet Microsoft.Windows.SDK.BuildTools into tools\sdk-buildtools\pkg (see README)." }
    ($c | Sort-Object FullName -Descending | Select-Object -First 1).FullName
}
$makeappx = Find-Tool 'makeappx.exe'

# --- identity
$id = Get-Content (Join-Path $msixSrc 'store_identity.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($id.name -like 'TODO*' -or $id.publisher -like 'CN=TODO*') {
    Write-Warning "store_identity.json still has placeholder identity. The package builds but the Store will reject it until you paste the Partner Center values."
}
if ($id.version -notmatch '^\d+\.\d+\.\d+\.0$') { Write-Warning "Store requires the 4th version part to be 0 (e.g. 1.0.0.0)." }
$ver3 = ($id.version -split '\.')[0..2] -join '.'
$esc = { param($s) [System.Security.SecurityElement]::Escape($s) }

# --- stage
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null
Copy-Item (Join-Path $app '*') $stage -Recurse -Force
Remove-Item (Join-Path $stage 'README_FOR_FRIENDS.txt') -ErrorAction SilentlyContinue   # describes the Setup/portable builds
Copy-Item (Join-Path $msixSrc 'Assets') (Join-Path $stage 'Assets') -Recurse -Force
$m = Get-Content (Join-Path $msixSrc 'AppxManifest.xml') -Raw -Encoding UTF8
$m = $m.Replace('{{NAME}}', (& $esc $id.name)).Replace('{{PUBLISHER}}', (& $esc $id.publisher)).Replace('{{PUBLISHER_DISPLAY_NAME}}', (& $esc $id.publisher_display_name)).Replace('{{VERSION}}', $id.version)
[System.IO.File]::WriteAllText((Join-Path $stage 'AppxManifest.xml'), $m, (New-Object System.Text.UTF8Encoding($false)))

# --- pack (with makeappx validation)
$out = Join-Path $dist "PhotoFinderPro-$ver3.msix"
if (Test-Path $out) { Remove-Item $out -Force }
& $makeappx pack /d $stage /p $out /o
if ($LASTEXITCODE -ne 0) { throw "makeappx pack failed ($LASTEXITCODE)" }
"{0}  ({1:N1} MB)" -f $out, ((Get-Item $out).Length / 1MB)

# --- optional local test signing (CurrentUser store only; no admin, no system trust changes)
if ($TestSign) {
    $signtool = Find-Tool 'signtool.exe'
    $cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $id.publisher -and $_.FriendlyName -eq 'PhotoFinderPro test signing' -and $_.NotAfter -gt (Get-Date) } | Select-Object -First 1
    if (-not $cert) {
        $cert = New-SelfSignedCertificate -Type Custom -Subject $id.publisher -KeyUsage DigitalSignature -FriendlyName 'PhotoFinderPro test signing' `
            -CertStoreLocation 'Cert:\CurrentUser\My' -KeyExportPolicy NonExportable `
            -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3', '2.5.29.19={text}')
    }
    $cer = Join-Path $root 'build\PhotoFinderPro-test.cer'
    Export-Certificate -Cert $cert -FilePath $cer | Out-Null     # public part only, for optional test-install
    $signed = Join-Path $dist "PhotoFinderPro-$ver3-testsigned.msix"
    Copy-Item $out $signed -Force
    & $signtool sign /fd SHA256 /sha1 $cert.Thumbprint /s My $signed
    if ($LASTEXITCODE -ne 0) { throw "signtool failed ($LASTEXITCODE)" }
    "{0}  (test-signed copy; public cert: {1})" -f $signed, $cer
}
