# Troubleshooting `dbt deps` TLS Failures Behind Zscaler

Date captured: 2026-04-01

## Summary

When `dbt deps` failed in this repo, the root cause was not dbt package metadata or network reachability. The failure came from Python/OpenSSL certificate validation when HTTPS traffic to `hub.getdbt.com` was intercepted by Zscaler.

The practical impact is important:

- `dbt deps` can fail with `SSLCertVerificationError`
- a failed `dbt deps` run may clean `dbt_packages/` before exiting
- later dbt commands then fail at compile time because packages are no longer installed

## Key Evidence

### Python/OpenSSL environment

Observed locally:

- Python: `3.12.12`
- OpenSSL: `OpenSSL 3.6.1 27 Jan 2026`
- `requests`: `2.32.5`

Relevant environment variables were already set:

```bash
REQUESTS_CA_BUNDLE=/opt/homebrew/opt/ca-certificates/share/ca-certificates/cacert.pem
SSL_CERT_FILE=/opt/homebrew/opt/ca-certificates/share/ca-certificates/cacert.pem
CURL_CA_BUNDLE=/opt/homebrew/opt/ca-certificates/share/ca-certificates/cacert.pem
```

Neither the Homebrew CA bundle nor `certifi` contained any `Zscaler` certificate entries.

### Direct Python reproduction

This reproduced the same failure outside dbt:

```bash
python3 - <<'PY'
import requests
requests.get("https://hub.getdbt.com/api/v1/index.json", timeout=20)
PY
```

Failure:

```text
SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

### TLS chain inspection

Inspecting the presented certificate chain showed HTTPS interception by Zscaler:

```bash
openssl s_client -connect hub.getdbt.com:443 -servername hub.getdbt.com -showcerts </dev/null
```

Important details from the captured output:

- leaf certificate subject: `CN=hub.cdn.getdbt.com, O=Zscaler Inc.`
- issuer: `Zscaler Intermediate Root CA (zscalerthree.net)`
- verification output included `unable to get local issuer certificate`

This means Python/OpenSSL was not trusting the Zscaler issuer chain used on this machine for outbound HTTPS inspection.

### `curl` comparison

The same endpoint succeeded with `curl`:

```bash
curl -I https://hub.getdbt.com/api/v1/index.json
```

Observed result:

- HTTP `200`

And `curl -V` showed:

```text
curl 8.7.1 ... libcurl/8.7.1 (SecureTransport) LibreSSL/3.3.6
```

That matters because macOS `curl` here is using `SecureTransport`, which relies on Apple trust settings differently from Python/OpenSSL. So:

- network reachability is fine
- the endpoint is fine
- the mismatch is specifically Python/OpenSSL trust, not general connectivity

## Working Diagnosis

The machine is behind Zscaler TLS interception, and Python/dbt is using an OpenSSL-based CA trust path that does not include the Zscaler root/intermediate chain trusted by macOS `curl`.

In short:

- `curl` works because it uses macOS trust handling
- `python requests` and `dbt deps` fail because they use OpenSSL CA files that do not trust the Zscaler issuer

## Repo Impact

During this incident:

- targeted dbt validation was still possible against an isolated DuckDB copy while packages were present
- `dbt deps` failed
- `dbt_packages/` was emptied by that failed run
- full dbt validation could not continue until package trust/install was repaired

## Implemented Fix (2026-04-01)

### What was done

The machine has the Zscaler root cert at:

```
~/Documents/Zscaler/ZscalerRootCertificate-2048-SHA256.pem
```

A merged CA bundle was created at `~/.certs/cacert.pem` (outside Homebrew's control) combining the standard Mozilla bundle with the Zscaler root:

```bash
mkdir -p ~/.certs
cat /opt/homebrew/opt/ca-certificates/share/ca-certificates/cacert.pem \
    ~/Documents/Zscaler/ZscalerRootCertificate-2048-SHA256.pem \
    > ~/.certs/cacert.pem
```

`~/.zshrc` was updated to point `SSL_CERT_FILE` at that merged bundle:

```bash
export SSL_CERT_FILE="$HOME/.certs/cacert.pem"
```

All other relevant vars (`REQUESTS_CA_BUNDLE`, `AWS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `GIT_SSL_CAINFO`) already derived from `SSL_CERT_FILE` in `.zshrc`, so no further changes were needed.

### Why `~/.certs/` and not the Homebrew path

The original `.zshrc` pointed at `/opt/homebrew/opt/ca-certificates/share/ca-certificates/cacert.pem`. Any `brew upgrade ca-certificates` (which runs as part of a general `brew upgrade`) overwrites that file and strips the Zscaler cert. `~/.certs/cacert.pem` is not touched by Homebrew.

### After a reboot

No manual steps needed. `.zshrc` is sourced automatically for every new interactive zsh shell, so `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` will point to the correct merged bundle immediately.

### If `dbt deps` fails mid-session in a fresh agent context

The agent's shell may not have sourced `.zshrc`. Run:

```bash
source ~/.zshrc
dbt deps
```

### If `brew upgrade ca-certificates` has been run since the fix

The merged bundle at `~/.certs/cacert.pem` is unaffected. No action needed.

However, if you want to pick up newly added Mozilla root CAs from the upgraded Homebrew bundle, regenerate the merged file:

```bash
cat /opt/homebrew/opt/ca-certificates/share/ca-certificates/cacert.pem \
    ~/Documents/Zscaler/ZscalerRootCertificate-2048-SHA256.pem \
    > ~/.certs/cacert.pem
```

Then verify the cert count went up (should be 145+ Mozilla roots + 1 Zscaler):

```bash
grep -c "BEGIN CERTIFICATE" ~/.certs/cacert.pem
```

### Important note

Just setting `REQUESTS_CA_BUNDLE` is not enough if the referenced PEM does not actually contain the Zscaler trust anchor. In the original incident, those variables were already set but the bundle still lacked the needed issuer — the variables pointed at the Homebrew bundle which had never had Zscaler appended to it.

## Validation Checklist After Fix

Once the CA issue is resolved:

```bash
dbt deps
dbt test
dbt source freshness
dbt build
PYTHONPATH=. pytest -q tests
```

## Fast Triage Commands

Use these when this happens again:

```bash
python3 - <<'PY'
import requests
print(requests.get("https://hub.getdbt.com/api/v1/index.json", timeout=20).status_code)
PY
```

```bash
openssl s_client -connect hub.getdbt.com:443 -servername hub.getdbt.com -showcerts </dev/null
```

```bash
curl -I https://hub.getdbt.com/api/v1/index.json
```

If Python fails but `curl` succeeds, suspect a Python/OpenSSL CA trust mismatch rather than a dbt-specific problem.
