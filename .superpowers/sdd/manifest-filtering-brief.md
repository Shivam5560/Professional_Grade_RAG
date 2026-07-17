# Manifest-Driven Application Filtering Brief

## Goal

Use one shared application-catalog state to hide disabled applications from persistent and prominent cross-application navigation outside the Header.

## Shared catalog ownership

- Add a client-side `AppCatalogProvider` around application content in the root layout.
- Refactor `useAppCatalog()` so all consumers read the provider's single catalog state and retry function rather than independently fetching.
- Keep latest-request-wins and unmount safety in the provider-owned loader.
- Keep the existing public `useAppCatalog()` contract used by Header and catalog pages. Fail clearly if it is used outside the provider.
- Provide a small typed helper for checking whether an application ID is enabled; it must return true only for a successful catalog containing that ID. Loading, empty, and error states must never expose stale application links.

## Navigation filtering

- `frontend/components/layout/Sidebar.tsx`
  - Show Workflows only when `career-studio` is enabled.
  - Show Developer only when `developer-studio` is enabled.
  - Knowledge Base and Settings remain in-scope/platform-local links for this sidebar.
- `frontend/components/aurasql/AuraSqlSidebar.tsx`
  - Dashboard remains unconditional.
  - Show RAG Chat only when `knowledge-studio` is enabled.
  - Show Developer only when `developer-studio` is enabled.
- `frontend/app/auth/page.tsx`
  - Show the clickable developer-profile navigation only when `developer-studio` is enabled. When disabled, retain non-clickable author attribution without advertising a route to the disabled application.
- `frontend/app/page.tsx`
  - Add an application ID to each launcher and render/prefetch only enabled launchers.
  - Map RAG Chat to `knowledge-studio`, AuraSQL to `aurasql`, Resume Studio and ResumeGen to `career-studio`, and Data Analysis to `data-analyst`.
  - The launcher count must reflect the filtered list; loading/error/empty states must not show disabled launchers and should provide a concise accessible catalog-state message rather than a blank misleading panel.

## Constraints

- Preserve existing routes, labels, callbacks, auth behavior, sidebar history behavior, styles, responsive layout, and platform links.
- Do not introduce a second catalog fetch per component.
- Do not convert internal links within an enabled application's own screens into manifest checks unless named above.
- Do not add or run tests, builds, lint, typecheck, or runtime commands. Static review only.
- Commit scoped production changes if Git writes are available.
