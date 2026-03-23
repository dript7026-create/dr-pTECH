param(
    [string]$WorkspaceRoot = "C:\Users\rrcar\Documents\drIpTECH",
    [string]$ReviewStamp = "",
    [ValidateSet("debug", "release")]
    [string]$ApkVariant = "debug",
    [switch]$SkipApk,
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"

$egosphereRoot = Join-Path $WorkspaceRoot "egosphere"
$deliverablesRoot = Join-Path $egosphereRoot "deliverables"
$androidRoot = Join-Path $WorkspaceRoot "urbden-android"
$assetsReviewDir = Join-Path $androidRoot "app\src\main\assets\review"
$apkPath = Join-Path $androidRoot ("app\build\outputs\apk\{0}\app-{0}.apk" -f $ApkVariant)
$packageApkName = "egosphere_review_app.apk"
$localPropertiesPath = Join-Path $androidRoot "local.properties"
$statusFileName = "DEPLOYMENT_STATUS.json"
$manifestFileName = "PACKAGE_MANIFEST.json"
$gradleTask = "assemble" + (Get-Culture).TextInfo.ToTitleCase($ApkVariant)

function Resolve-LatestReviewDir {
    param([string]$Root)

    $candidate = Get-ChildItem -Path $Root -Directory |
        Where-Object { $_.Name -like "external_client_review_*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1

    if ($null -eq $candidate) {
        throw "No external client review directory found under $Root"
    }

    return $candidate.FullName
}

function Assert-Exists {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "$Label not found: $Path"
    }
}

function Resolve-FirstExistingPath {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Resolve-LatestFileByPattern {
    param(
        [string]$Root,
        [string]$Pattern
    )

    if (-not (Test-Path $Root)) {
        return $null
    }

    return Get-ChildItem -Path $Root -Directory |
        Where-Object { $_.Name -like $Pattern } |
        Sort-Object Name -Descending |
        Select-Object -ExpandProperty FullName -First 1
}

if ([string]::IsNullOrWhiteSpace($ReviewStamp)) {
    $ReviewStamp = (Get-Date).ToString("yyyy-MM-dd")
}

$targetReviewName = "external_client_review_" + $ReviewStamp
$targetReviewDir = Join-Path $deliverablesRoot $targetReviewName

if (-not (Test-Path $targetReviewDir)) {
    $seedReviewDir = Resolve-LatestReviewDir -Root $deliverablesRoot
    Copy-Item $seedReviewDir $targetReviewDir -Recurse
}

$reviewDir = $targetReviewDir
$reviewName = Split-Path $reviewDir -Leaf
$zipPath = Join-Path $deliverablesRoot ($reviewName + ".zip")
$latestZipPath = Join-Path $deliverablesRoot "external_client_review_latest.zip"
$packageApkPath = Join-Path $reviewDir $packageApkName
$latestApkPath = Join-Path $deliverablesRoot "external_client_review_latest.apk"

$bootstrapRoot = Resolve-FirstExistingPath -Candidates @(
    (Join-Path $WorkspaceRoot ".android-bootstrap"),
    (Join-Path $WorkspaceRoot "android-bootstrap")
)

$jdkRoot = Resolve-LatestFileByPattern -Root (Join-Path $WorkspaceRoot ".jdk") -Pattern "jdk-*"
$pythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"

if ($null -eq $bootstrapRoot) {
    throw "Android bootstrap root not found under $WorkspaceRoot"
}

if ($null -eq $jdkRoot) {
    throw "No JDK installation found under " + (Join-Path $WorkspaceRoot ".jdk")
}

Assert-Exists -Path $pythonExe -Label "Workspace Python"

$sdkRoot = Join-Path $bootstrapRoot "android-sdk"
$gradleRoot = Resolve-LatestFileByPattern -Root $bootstrapRoot -Pattern "gradle-*"

if ($null -eq $gradleRoot) {
    throw "No Gradle installation found under $bootstrapRoot"
}

$gradleBat = Join-Path $gradleRoot "bin\gradle.bat"
$repoDir = Join-Path $reviewDir "repo"

$requiredDocs = @(
    "HANDOFF_NOTE.md",
    "CLIENT_EXEC_SUMMARY.md",
    "CLIENT_PRESENTATION_SCRIPT.md",
    "PRODUCT_BRIEF.md",
    "README.md",
    "REVIEW_GUIDE.md",
    "SHORT_NOTICE_DEPLOYMENT_CHECKLIST.md",
    "VALIDATION_SNAPSHOT.json"
)

foreach ($doc in $requiredDocs) {
    $docPath = Join-Path $reviewDir $doc
    Assert-Exists -Path $docPath -Label "Review document"
}

Assert-Exists -Path $reviewDir -Label "Review directory"
Assert-Exists -Path $repoDir -Label "Packaged repo directory"
Assert-Exists -Path (Join-Path $repoDir "egosphere.h") -Label "Core API header"
Assert-Exists -Path (Join-Path $repoDir "pipeline\README.md") -Label "Pipeline README"

New-Item -ItemType Directory -Force -Path $assetsReviewDir | Out-Null

$statusPath = Join-Path $reviewDir $statusFileName
$assetsStatusPath = Join-Path $assetsReviewDir $statusFileName
$manifestPath = Join-Path $reviewDir $manifestFileName
$assetsManifestPath = Join-Path $assetsReviewDir $manifestFileName

if (-not $SkipApk) {
    Assert-Exists -Path $jdkRoot -Label "JDK"
    Assert-Exists -Path $sdkRoot -Label "Android SDK"
    Assert-Exists -Path $gradleBat -Label "Gradle launcher"
}

if ($PreflightOnly) {
    Write-Host "PREFLIGHT_OK= true"
    Write-Host "PREFLIGHT_REVIEW_DIR=" $reviewDir
    Write-Host "PREFLIGHT_REVIEW_ZIP=" $zipPath
    Write-Host "PREFLIGHT_REVIEW_ZIP_LATEST=" $latestZipPath
    if (-not $SkipApk) {
        Write-Host "PREFLIGHT_APK=" $apkPath
        Write-Host "PREFLIGHT_APK_VARIANT=" $ApkVariant
        Write-Host "PREFLIGHT_GRADLE_TASK=" $gradleTask
    }
    exit 0
}

& $pythonExe (Join-Path $egosphereRoot "tools\generate_validation_snapshot.py") --review-dir $reviewDir --python-exe $pythonExe

foreach ($doc in $requiredDocs) {
    Copy-Item (Join-Path $reviewDir $doc) (Join-Path $assetsReviewDir $doc) -Force
}

if (-not $SkipApk) {
    $escapedSdk = $sdkRoot.Replace("\", "\\")
    Set-Content -Path $localPropertiesPath -Value ("sdk.dir=" + $escapedSdk) -Encoding ASCII

    $env:JAVA_HOME = $jdkRoot
    $env:ANDROID_SDK_ROOT = $sdkRoot
    $env:ANDROID_HOME = $sdkRoot

    Push-Location $androidRoot
    try {
        & $gradleBat $gradleTask --stacktrace
    }
    finally {
        Pop-Location
    }
}

$status = [ordered]@{
    prepared_at = (Get-Date).ToString("s")
    prepared_by = "egosphere/tools/prepare_client_preview.ps1"
    workspace_root = $WorkspaceRoot
    review_dir = $reviewDir
    review_zip_path = $zipPath
    review_zip_latest_path = $latestZipPath
    android_review_app = [ordered]@{
        variant = $ApkVariant
        gradle_task = $gradleTask
        path = $apkPath
        package_path = $packageApkPath
        latest_path = $latestApkPath
        requested = (-not $SkipApk)
        present = $false
    }
    bootstrap = [ordered]@{
        python_exe = $pythonExe
        jdk_root = $jdkRoot
        sdk_root = $sdkRoot
        gradle_root = $gradleRoot
    }
    required_docs = $requiredDocs
    notes = @(
        "Run the preparation script from the workspace root for short-notice rebuilds.",
        "Use script console output for exact artifact timestamps and byte counts.",
        "Use HANDOFF_NOTE.md as the fastest external starting point before the executive summary.",
        "Treat the Android APK as a review companion app rather than a runtime port.",
        "Set -ApkVariant release when you need the installable release build variant."
    )
}

$manifest = [ordered]@{
    package_name = $reviewName
    generated_at = $status.prepared_at
    package_root = $reviewDir
    review_zip_path = $zipPath
    review_zip_latest_path = $latestZipPath
    review_apk_variant = $ApkVariant
    review_apk_path = $packageApkPath
    review_apk_latest_path = $latestApkPath
    top_level_documents = @(
        "HANDOFF_NOTE.md",
        "CLIENT_EXEC_SUMMARY.md",
        "CLIENT_PRESENTATION_SCRIPT.md",
        "PRODUCT_BRIEF.md",
        "README.md",
        "REVIEW_GUIDE.md",
        "SHORT_NOTICE_DEPLOYMENT_CHECKLIST.md",
        "VALIDATION_SNAPSHOT.json",
        $statusFileName,
        $manifestFileName
    )
    key_repo_artifacts = @(
        "repo/README.md",
        "repo/egosphere.h",
        "repo/egosphere.c",
        "repo/smoke_test.c",
        "repo/tools/inspect_mindsphere_save.py",
        "repo/tools/game_pipeline.py",
        "repo/tools/drip3d_pipeline.py",
        "repo/tools/validate_pipeline.py",
        "repo/tools/run_pertinence_e2e.py",
        "repo/pipeline/README.md",
        "repo/pipeline/sample_project/game_project.json",
        "repo/pipeline/sample_project/game_project.drip3d.json",
        "repo/pipeline/out/validation/",
        "repo/pipeline/projects/pertinence_tribunal/",
        "repo/pipeline/out/pertinence_tribunal_validation/"
    )
    package_rules = @(
        "Use DEPLOYMENT_STATUS.json for current rebuild context.",
        "Use VALIDATION_SNAPSHOT.json for the validated technical snapshot.",
        "Use external_client_review_latest.zip as the stable short-notice archive path.",
        "Use -PreflightOnly to fail fast on missing package or toolchain prerequisites before rebuilds.",
        "Use -ApkVariant release to publish the installable release review APK into the stable alias path."
    )
}

if ((-not $SkipApk) -and (Test-Path $apkPath)) {
    $status.android_review_app.present = $true
    Copy-Item $apkPath $packageApkPath -Force
    Copy-Item $apkPath $latestApkPath -Force
}

$manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $manifestPath -Encoding UTF8
Copy-Item $manifestPath $assetsManifestPath -Force

$status | ConvertTo-Json -Depth 6 | Set-Content -Path $statusPath -Encoding UTF8
Copy-Item $statusPath $assetsStatusPath -Force

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

if (Test-Path $latestZipPath) {
    Remove-Item $latestZipPath -Force
}

Compress-Archive -Path (Join-Path $reviewDir "*") -DestinationPath $zipPath -Force
Copy-Item $zipPath $latestZipPath -Force

$zipItem = Get-Item $zipPath
$latestZipItem = Get-Item $latestZipPath

Write-Host "REVIEW_DIR=" $reviewDir
Write-Host "REVIEW_ZIP=" $zipItem.FullName
Write-Host "REVIEW_ZIP_BYTES=" $zipItem.Length
Write-Host "REVIEW_ZIP_UPDATED=" $zipItem.LastWriteTime.ToString("s")
Write-Host "REVIEW_ZIP_LATEST=" $latestZipItem.FullName
Write-Host "REVIEW_ZIP_LATEST_BYTES=" $latestZipItem.Length
Write-Host "REVIEW_ZIP_LATEST_UPDATED=" $latestZipItem.LastWriteTime.ToString("s")

if ((-not $SkipApk) -and (Test-Path $apkPath)) {
    $apkItem = Get-Item $apkPath
    $packageApkItem = Get-Item $packageApkPath
    $latestApkItem = Get-Item $latestApkPath
    Write-Host "APK_PATH=" $apkItem.FullName
    Write-Host "APK_BYTES=" $apkItem.Length
    Write-Host "APK_UPDATED=" $apkItem.LastWriteTime.ToString("s")
    Write-Host "PACKAGE_APK_PATH=" $packageApkItem.FullName
    Write-Host "PACKAGE_APK_BYTES=" $packageApkItem.Length
    Write-Host "PACKAGE_APK_UPDATED=" $packageApkItem.LastWriteTime.ToString("s")
    Write-Host "LATEST_APK_PATH=" $latestApkItem.FullName
    Write-Host "LATEST_APK_BYTES=" $latestApkItem.Length
    Write-Host "LATEST_APK_UPDATED=" $latestApkItem.LastWriteTime.ToString("s")
}

Write-Host "DEPLOYMENT_STATUS=" $statusPath
Write-Host "PACKAGE_MANIFEST=" $manifestPath
