import { notFound } from "next/navigation";
import { ShowcaseExperience } from "@/components/showcase/ShowcaseExperience";
import { ShowcaseProvider } from "@/components/showcase/ShowcaseProvider";
import { ShowcaseShell } from "@/components/showcase/ShowcaseShell";
import { getShowcaseScenario } from "@/lib/showcase/fixtures";

export function generateStaticParams() {
  return ["knowledge", "aurasql", "analysis", "career"].map((experience) => ({ experience }));
}

export default function Page({ params }: { params: { experience: string } }) {
  const scenario = getShowcaseScenario(params.experience);
  if (!scenario) notFound();
  return (
    <ShowcaseProvider scenario={scenario}>
      <ShowcaseShell>
        <ShowcaseExperience />
      </ShowcaseShell>
    </ShowcaseProvider>
  );
}
