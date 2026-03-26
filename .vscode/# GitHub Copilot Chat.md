# GitHub Copilot Chat

- Extension: 0.41.1 (prod)
- VS Code: 1.113.0 (cfbea10c5ffb233ea9177d34726e6056e89913dc)
- OS: win32 10.0.26200 x64
- GitHub Account: oneshotashton

## Network

User Settings:

```json
  "http.systemCertificatesNode": true,
  "github.copilot.advanced.debug.useElectronFetcher": true,
  "github.copilot.advanced.debug.useNodeFetcher": false,
  "github.copilot.advanced.debug.useNodeFetchFetcher": true
```

Connecting to <https://api.github.com>:

- DNS ipv4 Lookup: 140.82.114.5 (21 ms)
- DNS ipv6 Lookup: Error (6 ms): getaddrinfo ENOTFOUND api.github.com
- Proxy URL: None (1 ms)
- Electron fetch (configured): HTTP 200 (149 ms)
- Node.js https: HTTP 200 (156 ms)
- Node.js fetch: HTTP 200 (160 ms)

Connecting to <https://api.individual.githubcopilot.com/_ping>:

- DNS ipv4 Lookup: 140.82.112.22 (13 ms)
- DNS ipv6 Lookup: Error (4 ms): getaddrinfo ENOTFOUND api.individual.githubcopilot.com
- Proxy URL: None (1 ms)
- Electron fetch (configured): HTTP 200 (46 ms)
- Node.js https: HTTP 200 (157 ms)
- Node.js fetch: HTTP 200 (169 ms)

Connecting to <https://proxy.individual.githubcopilot.com/_ping>:

- DNS ipv4 Lookup: 138.91.182.224 (13 ms)
- DNS ipv6 Lookup: Error (4 ms): getaddrinfo ENOTFOUND proxy.individual.githubcopilot.com
- Proxy URL: None (2 ms)
- Electron fetch (configured): HTTP 200 (187 ms)
- Node.js https: HTTP 200 (196 ms)
- Node.js fetch: HTTP 200 (194 ms)

Connecting to <https://mobile.events.data.microsoft.com>: HTTP 404 (31 ms)
Connecting to <https://dc.services.visualstudio.com>: HTTP 404 (366 ms)
Connecting to <https://copilot-telemetry.githubusercontent.com/_ping>: HTTP 200 (175 ms)
Connecting to <https://telemetry.individual.githubcopilot.com/_ping>: HTTP 200 (173 ms)
Connecting to <https://default.exp-tas.com>: HTTP 400 (140 ms)

Number of system certificates: 123

## Documentation

In corporate networks: [Troubleshooting firewall settings for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-firewall-settings-for-github-copilot).
