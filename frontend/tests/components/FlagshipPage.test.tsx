import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import FlagshipPage from "@/app/page";

vi.mock("next/dynamic", () => ({ default: () => () => null }));
vi.mock("@/lib/store", () => ({ useAuthStore: () => ({ isAuthenticated: false }) }));
vi.mock("@/hooks/useCinematicEffects", () => ({
  useCinematicEffects: () => ({ enabled: false, visible: true }),
}));
vi.mock("@/components/theme/AppearanceControl", () => ({
  AppearanceControl: () => <button aria-label="Appearance">Appearance</button>,
}));
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

describe("FlagshipPage", () => {
  it("explains the product before presenting creator attribution", () => {
    render(<FlagshipPage />);
    const product = screen.getByRole("heading", { name: /intelligence, made tangible/i });
    const creator = screen.getByRole("heading", { name: /built end to end by shivam sourav/i });
    expect(product.compareDocumentPosition(creator) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("opens authentication from the flagship without a separate auth page", async () => {
    const user = userEvent.setup();
    render(<FlagshipPage />);
    expect(screen.getByRole("link", { name: /log in/i })).toHaveAttribute("href", "/?auth=login");
    await user.click(screen.getByRole("button", { name: /enter the workspace/i }));
    await waitFor(() =>
      expect(screen.getByRole("dialog", { name: /enter nexusmind/i })).toBeVisible(),
    );
    expect(screen.queryByRole("link", { name: /explore showcase/i })).not.toBeInTheDocument();
  });

  it.each(["Knowledge", "AuraSQL", "Analysis", "Career Studio"])("shows %s", (name) => {
    render(<FlagshipPage />);
    expect(screen.getByRole("heading", { name })).toBeInTheDocument();
  });
});
