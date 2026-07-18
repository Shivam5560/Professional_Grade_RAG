import { redirect } from "next/navigation";

export function generateStaticParams() {
  return ["knowledge", "aurasql", "analysis", "career"].map((experience) => ({ experience }));
}

export default function Page() {
  redirect("/");
}
