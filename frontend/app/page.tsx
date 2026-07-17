import { CapabilityStory } from "@/components/flagship/CapabilityStory";
import { CreatorStory } from "@/components/flagship/CreatorStory";
import { FlagshipHero } from "@/components/flagship/FlagshipHero";
import { PublicFooter } from "@/components/flagship/PublicFooter";
import { PublicHeader } from "@/components/flagship/PublicHeader";
import { TechnicalProof } from "@/components/flagship/TechnicalProof";

export default function FlagshipPage() {
  return (
    <div className="min-h-screen overflow-x-clip bg-background text-foreground">
      <PublicHeader />
      <main>
        <FlagshipHero />
        <CapabilityStory />
        <TechnicalProof />
        <CreatorStory />
      </main>
      <PublicFooter />
    </div>
  );
}
