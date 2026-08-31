param(
  [int[]]$ExtraWays = @(1, 2, 3, 4, 5, 6),
  [int]$BillionTries = 1,
  [int]$Seed = 1,
  [string]$OutputDir = "",
  [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$binDir = Join-Path $root "bin"
$srcDir = Join-Path $root "src"

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
  if ($SmokeTest) {
    $OutputDir = "results/comparison_smoke"
  } else {
    $OutputDir = "results/comparison_1Bn"
  }
}

$outDir = Join-Path $root $OutputDir
$rawDir = Join-Path $outDir "raw_results"

New-Item -ItemType Directory -Force -Path $binDir | Out-Null
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

$commonFlags = @("-std=c++0x", "-O3")
$smokeDefines = @()
if ($SmokeTest) {
  $smokeDefines = @(
    "-DCUSTOM_BILLION_TRIES=1000000ULL",
    "-DCUSTOM_HUNDRED_MILLION_TRIES=100000ULL"
  )
}

$builds = @(
  @{
    Name = "mirage"
    Source = (Join-Path $srcDir "security_mirage.cpp")
    Binary = (Join-Path $binDir "mirage.o")
  },
  @{
    Name = "maya"
    Source = (Join-Path $srcDir "security_maya.cpp")
    Binary = (Join-Path $binDir "maya6Ways.o")
  },
  @{
    Name = "ssl_local_random"
    Source = (Join-Path $srcDir "bucketsNballs_SSL_LocalRandom_NBn.cpp")
    Binary = (Join-Path $binDir "mirage_ssl_local_random.o")
  }
)

foreach ($build in $builds) {
  Write-Host "Building $($build.Name)..."
  & g++ @commonFlags @smokeDefines $build.Source "-o" $build.Binary
  if ($LASTEXITCODE -ne 0) {
    throw "Build failed for $($build.Name)"
  }
}

foreach ($extra in $ExtraWays) {
  foreach ($build in $builds) {
    $outputName = "{0}.{1}extraways.{2}Bn.seed{3}.out" -f $build.Name, $extra, $BillionTries, $Seed
    $outputPath = Join-Path $rawDir $outputName
    Write-Host "Running $($build.Name) extra=$extra billion_tries=$BillionTries seed=$Seed"
    $cmdLine = '"' + $build.Binary + '" ' + $extra + ' ' + $BillionTries + ' ' + $Seed +
      ' > "' + $outputPath + '" 2>&1'
    & cmd /c $cmdLine
    if ($LASTEXITCODE -ne 0) {
      throw "Run failed for $($build.Name) extra=$extra"
    }
  }
}

Write-Host "Parsing comparison CSVs..."
& python (Join-Path $root "scripts/export_security_compare_csv.py") `
  --input-dir $rawDir `
  --output-dir $outDir

if ($LASTEXITCODE -ne 0) {
  throw "CSV export failed"
}

Write-Host "Done. Results are in $outDir"
