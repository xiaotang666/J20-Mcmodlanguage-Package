# J20-Mcmodlanguage-Package 资源包图标生成脚本
# 设计语言：平面印刷海报（色块分割 + 反转套色字形），零渐变/零发光/零投影/零装饰点
# 配色：油墨黑 + 米白 + 朱红（单一强调色）
# 输出：branding/pack.png（256x256，Minecraft 资源包图标）
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File branding/gen_pack_logo.ps1
Add-Type -AssemblyName System.Drawing

$W = 256
$bmp = New-Object System.Drawing.Bitmap $W, $W
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.TextRenderingHint = 'AntiAlias'

# ---------- 色板 ----------
$ink   = [System.Drawing.Color]::FromArgb(255, 23, 26, 31)      # 油墨黑（非纯黑）
$paper = [System.Drawing.Color]::FromArgb(255, 242, 239, 232)   # 米白
$verm  = [System.Drawing.Color]::FromArgb(255, 226, 67, 44)     # 朱红（唯一强调色）
$SPLIT = 152                                                     # 色场交界 x（J2 / 0 之间）

# ---------- 色场：满幅油墨黑 + 左侧米白块（不对称分割） ----------
$g.Clear($ink)
$g.FillRectangle([System.Drawing.SolidBrush]::new($paper), 0, 0, $SPLIT, $W)

# ---------- 底部朱红基线条（通栏，压住版面） ----------
$g.FillRectangle([System.Drawing.SolidBrush]::new($verm), 0, 242, $W, 10)

$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = 'Center'
$sf.LineAlignment = 'Center'
$sf.FormatFlags = [System.Drawing.StringFormatFlags]::NoWrap

# ---------- 主字 J20：逐字固定定位（绕开 GDI+ 文本测量误差），字色跨界反转 ----------
# J(ink) 2(ink) | 0(paper) —— 交界落在 2 与 0 之间，反转一目了然
$fontJ = [System.Drawing.Font]::new('Arial Black', [float]60, [System.Drawing.FontStyle]::Regular)
$chars = @(@('J', 22), @('2', 88), @('0', 154))

$g.SetClip([System.Drawing.Rectangle]::new(0, 0, $SPLIT, $W))
foreach ($c in $chars) {
    $r = New-Object System.Drawing.RectangleF $c[1], 40, 62, 116
    $g.DrawString($c[0], $fontJ, ([System.Drawing.SolidBrush]::new($ink)), $r, $sf)
}
$g.SetClip([System.Drawing.Rectangle]::new($SPLIT, 0, ($W - $SPLIT), $W))
foreach ($c in $chars) {
    $r = New-Object System.Drawing.RectangleF $c[1], 40, 62, 116
    $g.DrawString($c[0], $fontJ, ([System.Drawing.SolidBrush]::new($paper)), $r, $sf)
}
$g.ResetClip()

# ---------- 副名 汉化资源包：跨越交界反转（"包"字被交界切开换色） ----------
$family = New-Object System.Drawing.FontFamily 'Microsoft YaHei UI'
$fontC = [System.Drawing.Font]::new($family, [float]22, [System.Drawing.FontStyle]::Bold)
$rC = New-Object System.Drawing.RectangleF 16, 184, 176, 40

$g.SetClip([System.Drawing.Rectangle]::new(0, 0, $SPLIT, $W))
$g.DrawString('汉化资源包', $fontC, ([System.Drawing.SolidBrush]::new($ink)), $rC, $sf)
$g.SetClip([System.Drawing.Rectangle]::new($SPLIT, 0, ($W - $SPLIT), $W))
$g.DrawString('汉化资源包', $fontC, ([System.Drawing.SolidBrush]::new($paper)), $rC, $sf)
$g.ResetClip()

# ---------- 右下小字：完全落在油墨色场内，右对齐 ----------
$fontS = [System.Drawing.Font]::new('Consolas', [float]7, [System.Drawing.FontStyle]::Regular)
$sfR = New-Object System.Drawing.StringFormat
$sfR.Alignment = 'Far'
$sfR.LineAlignment = 'Center'
$sfR.FormatFlags = [System.Drawing.StringFormatFlags]::NoWrap
$brushS = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 139, 141, 145))
$rS = New-Object System.Drawing.RectangleF 176, 184, 72, 40
$g.DrawString('Vault Patcher', $fontS, $brushS, $rS, $sfR)

$out = Join-Path $PSScriptRoot 'pack.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "saved: $out"
