import { render, screen } from "@testing-library/react";

import { CinematicBackdrop } from "@/components/cinematic/CinematicBackdrop";

vi.mock("@/hooks/useCinematicEffects", () => ({
  useCinematicEffects: () => ({ enabled: true, visible: true }),
}));

it("renders local dark and light cinematic sources with a readability veil", () => {
  render(
    <CinematicBackdrop
      media={{
        dark: "/dark.webp",
        light: "/light.webp",
        alt: "Authored scene",
        focalPoint: "70% 40%",
      }}
    />,
  );

  expect(screen.getByAltText("Authored scene")).toHaveAttribute(
    "src",
    expect.stringContaining("dark.webp"),
  );
  expect(screen.getByTestId("cinematic-veil")).toBeInTheDocument();
});
