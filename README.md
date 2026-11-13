# outpace-stream/actions

Shared GitHub Actions for the outpace-stream repositories. Each action lives in
its own directory and is versioned with the repository tags: `v1` is the moving
major tag, `v1.x.y` tags are immutable releases.

| Action | Purpose |
| --- | --- |
| [`identifier-hygiene`](identifier-hygiene) | Fail-closed scan for real AceStream content ids and infohashes |

## identifier-hygiene

Rejects any non-placeholder 40-hex value (a real content id or infohash) in a
repository's tracked files, and hard-blocks committing the private
`acestream-ids.txt` registry. It never reads the registry. Stream names are not
machine-detected and stay review-enforced.

```yaml
jobs:
  identifiers:
    name: acestream identifier hygiene
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - uses: outpace-stream/actions/identifier-hygiene@v1
```

Keep the job name if a ruleset requires the `acestream identifier hygiene`
check: a composite action runs as a step, so the check is still named after the
caller's job.

Inputs:

| Input | Default | Meaning |
| --- | --- | --- |
| `allowlist` | `tools/hygiene/allowed-identifiers.txt` | Allowlist path relative to the repository root. A missing file means an empty allowlist. |
| `working-directory` | `.` | Directory inside the checkout to scan from. |

The allowlist stays in each consuming repository, because its entries vouch for
hashes in that repository's own content. One value per line, followed by a
justification:

```text
# <40-hex>  <justification>
0123456789abcdef0123456789abcdef01234567  example only: placeholders are exempt anyway
```

Where a 40-hex string is syntactically required, use the synthetic placeholder
`0123456789abcdef0123456789abcdef01234567`.

### Running it locally

The checker is a single standard-library Python file and scans the git
repository of the current directory:

```sh
curl -fsSL https://raw.githubusercontent.com/outpace-stream/actions/v1/identifier-hygiene/check_identifiers.py | python3 -
```

Pass `--staged` to scan the index instead of all tracked files, and
`--allowlist PATH` (before other arguments) for a non-default allowlist.
outpace-engine's `.githooks/pre-commit` downloads the version its CI pins,
caches it under the git directory and blocks commits when no copy is available.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 identifier-hygiene/check_identifiers.py
```

A change to an action's behaviour gets a new `v1.x.y` tag and moves `v1`. A
breaking change to any action starts `v2`.
