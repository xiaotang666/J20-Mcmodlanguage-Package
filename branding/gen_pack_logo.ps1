# J20-Mcmodlanguage-Package 资源包图标生成脚本
# 输出：branding/pack.png（256x256，Minecraft 资源包图标）
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File branding/gen_pack_logo.ps1
Add-Type -AssemblyName System.Drawing

$W = 256
$bmp = New-Object System.Drawing.Bitmap $W, $W
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.TextRenderingHint = 'AntiAlias'

# ---------- 背景：深海军蓝 -> 亮天蓝 对角渐变 ----------
$rect = New-Object System.Drawing.Rectangle 0, 0, $W, $W
$bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect,
    ([System.Drawing.Color]::FromArgb(255, 6, 26, 60)),
    ([System.Drawing.Color]::FromArgb(255, 34, 118, 232)), 45
$g.FillRectangle($bg, $rect)

# ---------- 装饰：右上两道斜向光带（低透明度） ----------
$streak = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(20, 255, 255, 255))
$g.FillPolygon($streak, @(
    (New-Object System.Drawing.Point 176, 0), (New-Object System.Drawing.Point 256, 0),
    (New-Object System.Drawing.Point 256, 74), (New-Object System.Drawing.Point 202, 0)))
$g.FillPolygon($streak, @(
    (New-Object System.Drawing.Point 226, 0), (New-Object System.Drawing.Point 256, 0),
    (New-Object System.Drawing.Point 256, 28), (New-Object System.Drawing.Point 240, 0)))
# 左下呼应的小光带
$g.FillPolygon($streak, @(
    (New-Object System.Drawing.Point 0, 210), (New-Object System.Drawing.Point 52, 256),
    (New-Object System.Drawing.Point 0, 256)))

# ---------- 装饰：底部三粒渐次的冰蓝像素点 ----------
foreach ($p in @(@(64, 224, 8, 120), @(124, 224, 8, 180), @(184, 224, 8, 235))) {
    $b = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb($p[3], 111, 195, 255))
    $g.FillRectangle($b, $p[0], $p[1], $p[2], $p[2])
}

# ---------- 细圆角内描边 ----------
function Get-RoundedRect([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $gp = New-Object System.Drawing.Drawing2D.GraphicsPath
    $gp.AddArc($x, $y, 2 * $r, 2 * $r, 180, 90)
    $gp.AddArc($x + $w - 2 * $r, $y, 2 * $r, 2 * $r, 270, 90)
    $gp.AddArc($x + $w - 2 * $r, $y + $h - 2 * $r, 2 * $r, 2 * $r, 0, 90)
    $gp.AddArc($x, $y + $h - 2 * $r, 2 * $r, 2 * $r, 90, 90)
    $gp.CloseFigure()
    return $gp
}
$borderPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(90, 255, 255, 255)), 2.5
$g.DrawPath($borderPen, (Get-RoundedRect 13 13 230 230 18))

$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = 'Center'
$sf.LineAlignment = 'Center'

# ---------- 标题 J20（投影 + 主体） ----------
$family = New-Object System.Drawing.FontFamily 'Microsoft YaHei UI'
$font1 = [System.Drawing.Font]::new($family, [float]74, [System.Drawing.FontStyle]::Bold)
$shadow = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(95, 0, 12, 36))
$r1s = New-Object System.Drawing.RectangleF 3, 34, $W, 104
$g.DrawString('J20', $font1, $shadow, $r1s, $sf)
$r1 = New-Object System.Drawing.RectangleF 0, 30, $W, 104
$g.DrawString('J20', $font1, ([System.Drawing.Brushes]::White), $r1, $sf)

# ---------- 标题下冰蓝分隔线 ----------
$lineBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(235, 111, 195, 255))
$g.FillRectangle($lineBrush, 88, 136, 80, 3)

# ---------- 副标题 ----------
$font2 = [System.Drawing.Font]::new($family, [float]28, [System.Drawing.FontStyle]::Bold)
$brush2 = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 227, 242, 255))
$r2 = New-Object System.Drawing.RectangleF 0, 150, $W, 50
$g.DrawString('汉化资源包', $font2, $brush2, $r2, $sf)

# ---------- 底部小字 ----------
$font3 = [System.Drawing.Font]::new($family, [float]12, [System.Drawing.FontStyle]::Regular)
$brush3 = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 168, 205, 245))
$r3 = New-Object System.Drawing.RectangleF 0, 198, $W, 30
$g.DrawString('i18n  ×  Vault Patcher', $font3, $brush3, $r3, $sf)

$out = Join-Path $PSScriptRoot 'pack.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "saved: $out"
