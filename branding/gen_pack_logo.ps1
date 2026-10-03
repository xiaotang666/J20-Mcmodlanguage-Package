# J20-Mcmodlanguage-Package 资源包图标生成脚本
# 输出：branding/pack.png（256x256，Minecraft 资源包图标）
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File branding/gen_pack_logo.ps1
Add-Type -AssemblyName System.Drawing

$W = 256
$bmp = New-Object System.Drawing.Bitmap $W, $W
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.TextRenderingHint = 'AntiAlias'

# 背景：深靛 -> 紫罗兰 对角渐变
$rect = New-Object System.Drawing.Rectangle 0, 0, $W, $W
$bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect,
    ([System.Drawing.Color]::FromArgb(255, 36, 22, 74)),
    ([System.Drawing.Color]::FromArgb(255, 124, 58, 237)), 45
$g.FillRectangle($bg, $rect)

# 像素装饰点（MC 像素风）
$px = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(42, 255, 214, 236))
foreach ($p in @(@(30, 42, 10), @(208, 38, 14), @(38, 198, 12), @(202, 194, 10), @(122, 30, 8), @(152, 212, 9))) {
    $g.FillRectangle($px, $p[0], $p[1], $p[2], $p[2])
}

# 内边框
$pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(180, 255, 214, 236)), 5
$g.DrawRectangle($pen, 12, 12, $W - 25, $W - 25)

$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = 'Center'
$sf.LineAlignment = 'Center'

# 标题 J20（带投影）
$family = New-Object System.Drawing.FontFamily 'Microsoft YaHei UI'
$font1 = [System.Drawing.Font]::new($family, [float]78, [System.Drawing.FontStyle]::Bold)
$shadow = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(110, 0, 0, 0))
$r1s = New-Object System.Drawing.RectangleF 4, 26, $W, 110
$g.DrawString('J20', $font1, $shadow, $r1s, $sf)
$r1 = New-Object System.Drawing.RectangleF 0, 22, $W, 110
$g.DrawString('J20', $font1, ([System.Drawing.Brushes]::White), $r1, $sf)

# 副标题
$font2 = [System.Drawing.Font]::new($family, [float]30, [System.Drawing.FontStyle]::Bold)
$brush2 = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 255, 214, 236))
$r2 = New-Object System.Drawing.RectangleF 0, 130, $W, 52
$g.DrawString('汉化资源包', $font2, $brush2, $r2, $sf)

# 底部小字
$font3 = [System.Drawing.Font]::new($family, [float]13, [System.Drawing.FontStyle]::Regular)
$brush3 = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 203, 184, 240))
$r3 = New-Object System.Drawing.RectangleF 0, 188, $W, 32
$g.DrawString('i18n  x  Vault Patcher', $font3, $brush3, $r3, $sf)

$out = Join-Path $PSScriptRoot 'pack.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "saved: $out"
