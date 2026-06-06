# Browser Interaction Coverage Matrix

This matrix is a hard execution contract for `06-dynamic-browser-burp-mcp`. It closes the false-dynamic-validation failure mode where an audit claims browser coverage without real clicking, scrolling, role switching or network evidence.

## Required interaction classes

A browser run must cover or explicitly mark unavailable:

- open page;
- click visible links and buttons;
- expand menus and dropdowns;
- hover controlled elements;
- switch tabs;
- open modals;
- scroll to page bottom and trigger infinite loading;
- perform search;
- change filters;
- paginate;
- trigger safe form validation;
- trigger upload UI with an empty harmless sample only;
- mutate path, query and hash for client-side routes;
- refresh deep routes;
- visit 403, 404 and 500/error pages;
- switch anonymous, low-privilege, normal, admin and tenant contexts when test accounts are provided.

## Evidence classes

Each covered row should record, when available:

- HAR entry pointer;
- request and response summary;
- screenshot pointer;
- DOM snapshot pointer;
- console log pointer;
- storage snapshot pointer;
- cookie snapshot pointer;
- WebSocket/SSE/GraphQL pointer;
- new JS chunk and new API endpoint observed during the interaction.

## Runtime missing rule

If Playwright, browser runtime, Burp or MCP is unavailable, the output must state `runtime_missing` and the reason. It is forbidden to convert static-only evidence into dynamic validation.

## Confirmation rule

`confirmed` requires non-destructive dynamic evidence, negative control, role/tenant context and evidence manifest validation. A browser matrix with missing click/scroll/input/role-tenant evidence blocks confirmation unless the target genuinely has no such UI and the reason is recorded.
