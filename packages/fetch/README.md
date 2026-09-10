# @xpage/fetch

Thin integration boundary for resilient website fetching.

Source inspiration: `Emodv/l2agent`.

Do not vendor the Go repository here. X.page's scanner currently uses native `fetch` with timeout and redirects. If stronger anti-bot handling, retries, or rendering become necessary, expose them behind a small adapter in this package so the X.page brand and API contract stay stable.
