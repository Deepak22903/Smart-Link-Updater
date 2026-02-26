"use client";

import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/dashboard-layout";

const PostsList = dynamic(() => import("@/components/posts-list").then((m) => ({ default: m.PostsList })), {
  ssr: false,
});

export default function PostsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-1 mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Posts</h1>
        <p className="text-sm text-slate-500">
          Manage your content posts, extractors, and link configurations.
        </p>
      </div>
      <PostsList />
    </DashboardLayout>
  );
}
