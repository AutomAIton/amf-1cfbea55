# Run this in your own PowerShell window. It asks for the GitHub token (typing is hidden),
# saves it on the VPS in a root-only file, and does one live check. The token never touches disk here.
$ErrorActionPreference = 'Stop'
$sec = Read-Host 'Paste the GitHub token (hidden)' -AsSecureString
$tok = [System.Net.NetworkCredential]::new('', $sec).Password
if ($tok -notmatch '^(github_pat_|ghp_)[A-Za-z0-9_]{20,}$') { throw 'That does not look like a GitHub token.' }
$ssh = "$env:SystemRoot\System32\OpenSSH\ssh.exe"
$o = @('-i', "$env:USERPROFILE\.ssh\certpath_admin", '-p', '2222', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=3')
"GITHUB_TOKEN=$tok" | & $ssh @o certpath@10.100.0.1 'sudo -n tee /etc/ai-morning/github.env >/dev/null && sudo -n sed -i "s/\r$//" /etc/ai-morning/github.env && sudo -n chmod 600 /etc/ai-morning/github.env && echo SAVED'
# Live check without starting a build: ask GitHub to run a branch that does not exist.
# 422 = the token CAN start workflows (good). 403 = missing Actions write. 401/404 = wrong or mis-scoped token.
$check = 'T=$(sudo -n grep -oP "(?<=GITHUB_TOKEN=).*" /etc/ai-morning/github.env); curl -s -o /dev/null -w "GitHub check: HTTP %{http_code} (422 = good, 403 = no Actions write, 401/404 = bad token)\n" -X POST -H @<(printf "Authorization: Bearer %s\n" "$T") -H "Accept: application/vnd.github+json" https://api.github.com/repos/AutomAIton/amf-1cfbea55/actions/workflows/daily.yml/dispatches -d ''{"ref":"no-such-branch-check"}'''
& $ssh -n @o certpath@10.100.0.1 $check
$tok = $null
