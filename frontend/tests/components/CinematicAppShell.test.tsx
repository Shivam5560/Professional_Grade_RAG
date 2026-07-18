import { render, screen } from "@testing-library/react";

import { CinematicAppShell } from "@/components/shell/CinematicAppShell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/aurasql",
  useRouter: () => ({ push: vi.fn() }),
}));
vi.mock("@/components/layout/JobCenter", () => ({
  JobCenter: () => <button aria-label="Open job center">Jobs</button>,
}));
vi.mock("@/components/theme/AppearanceControl", () => ({
  AppearanceControl: () => <button aria-label="Appearance">Appearance</button>,
}));
vi.mock("@/hooks/useCinematicEffects", () => ({
  useCinematicEffects: () => ({ enabled: false, visible: true }),
}));
vi.mock("@/lib/store", () => ({
  useAuthStore: () => ({ user: null, logout: vi.fn() }),
}));

it("shows application navigation and only the active application's local submenu", () => {
  render(
    <CinematicAppShell
      catalog={{
        status: "success",
        apps: [],
        error: null,
        retry: vi.fn(),
      } as never}
    >
      <div>AuraSQL work</div>
    </CinematicAppShell>,
  );

  expect(
    screen.getByRole("navigation", { name: "Applications" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("navigation", { name: "AuraSQL sections" }),
  ).toBeInTheDocument();
  expect(screen.getByText("AuraSQL work")).toBeInTheDocument();
  expect(
    screen.queryByRole("link", { name: "Analysis history" }),
  ).not.toBeInTheDocument();
});
