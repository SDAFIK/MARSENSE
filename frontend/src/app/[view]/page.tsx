import { notFound } from "next/navigation";
import MissionWorkspace from "@/components/mission-workspace";
import type { View } from "@/lib/types";
export function generateStaticParams() {
  return ["mission", "astronaut", "evidence", "memory", "comparison", "intelligence"].map(
    (view) => ({ view }),
  );
}
export default async function Page({
  params,
}: {
  params: Promise<{ view: string }>;
}) {
  const { view } = await params;
  if (
    !["mission", "astronaut", "evidence", "memory", "comparison", "intelligence"].includes(view)
  )
    notFound();
  return <MissionWorkspace view={view as View} />;
}
