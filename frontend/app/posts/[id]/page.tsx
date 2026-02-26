"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard-layout";

const PostDetail = dynamic(
  () =>
    import("@/components/post-detail").then((m) => ({
      default: m.PostDetail,
    })),
  { ssr: false }
);

export default function PostDetailPage() {
  const params = useParams();
  const postId = Number(params.id) || 1;

  return (
    <DashboardLayout>
      <PostDetail postId={postId} />
    </DashboardLayout>
  );
}
