const PUBLIC_ROUTES = new Set(["/", "/auth", "/developer", "/showcase"]);

export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.has(pathname) || pathname.startsWith("/showcase/");
}
