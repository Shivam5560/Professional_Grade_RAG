import { redirect } from "next/navigation";

export default function AuthRedirect(): JSX.Element {
  redirect("/?auth=login");
}
