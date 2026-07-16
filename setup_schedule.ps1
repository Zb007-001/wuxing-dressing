# 五行穿衣颜色推荐 - Windows 定时任务安装脚本
# 每天早上 9:00 自动推送到微信

$taskName = "WuxingDressingDailyPush"
$batPath = "E:\codex\Workspace\Project_09_五行穿衣颜色推荐\daily_push.bat"

# 删除旧任务（如果存在）
schtasks /delete /tn $taskName /f 2>$null

# 创建新任务：每天早上 9:00 执行
schtasks /create /tn $taskName /tr "`"$batPath`"" /sc daily /st 09:00 /f

Write-Host ""
Write-Host "=== 定时任务已创建 ===" -ForegroundColor Green
Write-Host "任务名称: $taskName"
Write-Host "执行时间: 每天早上 09:00"
Write-Host "批处理路径: $batPath"
Write-Host ""

schtasks /query /tn $taskName /fo LIST /v | Select-String "TaskName|Status|Next Run Time|Schedule"
