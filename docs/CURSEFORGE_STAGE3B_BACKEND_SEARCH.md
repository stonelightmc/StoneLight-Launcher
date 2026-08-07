# CurseForge Stage 3b backend search optimization

This snapshot expects the VPS backend to be updated to `StoneLight CurseForge Proxy v0.3.0`.

## Change

The launcher no longer verifies CurseForge file compatibility project-by-project on the client side.

Instead it calls:

```text
GET /api/v1/cf/search-compatible
```

The backend performs broad + strict search, ranks results, checks compatible files in parallel and returns only installable projects.

## Expected result

CurseForge search should become noticeably faster after the first request. Repeated identical requests can be served from the backend in-memory cache.
