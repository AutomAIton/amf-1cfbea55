# Run this in your own PowerShell window. It asks for the GitHub token (typing is hidden),
# saves it on the VPS in a root-only file, and does one live check. The token never touches disk here.
$ErrorActionPreference = 'Stop'
$sec = Read-Host 'Paste the GitHub token (hidden)' -AsSecureString
$tok = [System.Net.NetworkCredential]::new('', $sec).Password
if ($tok -notmatch '^(github_pat_|ghp_)[A-Za-z0-9_]{20,}$') { throw 'That does not look like a GitHub token.' }
$ssh = "$env:SystemRoot\System32\OpenSSH\ssh.exe"
$o = @('-i', "$env:USERPROFILE\.ssh\certpath_admin", '-p', '2222', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=3')
"GITHUB_TOKEN=$tok" | & $ssh @o certpath@10.100.0.1 'sudo -n tee /etc/ai-morning/github.env >/dev/null && sudo -n sed -i "s/\r$//" /etc/ai-morning/github.env && sudo -n chmod 600 /etc/ai-morning/github.env && echo SAVED'
# Live check: the token must be able to read this repo's workflow runs (prints the HTTP code only).
$check = 'T=$(sudo -n grep -oP "(?<=GITHUB_TOKEN=).*" /etc/ai-morning/github.env); curl -s -o /dev/null -w "GitHub check: HTTP %{http_code} (200 = good)\n" -H @<(printf "Authorization: Bearer %s\n" "$T") https://api.github.com/repos/AutomAIton/amf-1cfbea55/actions/workflows/daily.yml/runs?per_page=1'
& $ssh -n @o certpath@10.100.0.1 $check
$tok = $null
