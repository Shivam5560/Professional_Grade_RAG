import { render, screen } from "@testing-library/react";
import FlagshipPage from "@/app/page";

vi.mock("next/dynamic", () => ({ default: () => () => null }));
vi.mock("@/lib/store", () => ({ useAuthStore: () => ({ isAuthenticated: false }) }));
vi.mock("@/hooks/useCinematicEffects", () => ({
  useCinematicEffects: () => ({ enabled: false, visible: true }),
}));
vi.mock("@/components/theme/AppearanceControl", () => ({
  AppearanceControl: () => <button aria-label="Appearance">Appearance</button>,
}));

describe("FlagshipPage", () => {
  it("explains the product before presenting creator attribution", () => {
    render(<FlagshipPage />);
    const product = screen.getByRole("heading", { name: /intelligence, made tangible/i });
    const creator = screen.getByRole("heading", { name: /built end to end by shivam sourav/i });
    expect(product.compareDocumentPosition(creator) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("offers showcase and live-workspace paths", () => {
    render(<FlagshipPage />);
    expect(screen.getByRole("link", { name: /explore showcase/i })).toHaveAttribute("href", "/showcase");
    expect(screen.getByRole("link", { name: /launch live workspace/i })).toHaveAttribute("href", "/auth");
  });

  it.each(["Knowledge", "AuraSQL", "Analysis", "Career Studio"])("shows %s", (name) => {
    render(<FlagshipPage />);
    expect(screen.getByRole("heading", { name })).toBeInTheDocument();
  });
});
