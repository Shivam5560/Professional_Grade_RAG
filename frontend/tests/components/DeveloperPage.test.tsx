import { render, screen } from "@testing-library/react";
import DeveloperPage from "@/app/developer/page";

vi.mock("@/lib/store", () => ({ useAuthStore: () => ({ isAuthenticated: false }) }));
vi.mock("@/components/theme/AppearanceControl", () => ({
  AppearanceControl: () => <button aria-label="Appearance">Appearance</button>,
}));

describe("DeveloperPage", () => {
  it("states solo ownership and shows engineering breadth", () => {
    render(<DeveloperPage />);
    expect(screen.getByRole("heading", { name: /shivam sourav/i })).toBeInTheDocument();
    expect(screen.getByText(/solely designed and developed/i)).toBeInTheDocument();
    for (const area of ["Product design", "RAG systems", "Data intelligence", "Platform engineering"]) {
      expect(screen.getByRole("heading", { name: area })).toBeInTheDocument();
    }
  });

  it("returns visitors to product proof and showcase", () => {
    render(<DeveloperPage />);
    expect(screen.getByRole("link", { name: /view product/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /explore showcase/i })).toHaveAttribute("href", "/showcase");
    expect(screen.getByRole("link", { name: /github/i })).toHaveAttribute("href", "https://github.com/Shivam5560");
    expect(screen.getByRole("link", { name: /linkedin/i })).toHaveAttribute("href", "https://linkedin.com/in/shivam-sourav-b889aa204/");
  });
});
