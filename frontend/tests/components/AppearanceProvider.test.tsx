import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AppearanceProvider, useAppearance } from "@/components/theme/AppearanceProvider";
import { AppearanceControl } from "@/components/theme/AppearanceControl";

function Probe() {
  const appearance = useAppearance();
  return <output>{appearance.preference}:{appearance.resolvedTheme}</output>;
}

describe("AppearanceProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    window.matchMedia = ((query: string) => ({
      matches: query.includes("dark"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })) as unknown as typeof window.matchMedia;
  });

  it("starts from system and resolves the media preference", () => {
    render(<AppearanceProvider><Probe /></AppearanceProvider>);
    expect(screen.getByText("system:dark")).toBeInTheDocument();
  });

  it("lets the user select light mode accessibly", async () => {
    render(<AppearanceProvider><AppearanceControl /><Probe /></AppearanceProvider>);
    await userEvent.click(screen.getByRole("button", { name: /appearance/i }));
    await userEvent.click(screen.getByRole("menuitemradio", { name: /light/i }));
    expect(screen.getByText("light:light")).toBeInTheDocument();
    expect(document.documentElement).not.toHaveClass("dark");
  });
});
