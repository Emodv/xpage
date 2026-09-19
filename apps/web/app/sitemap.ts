import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://cityverified.ca",
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: "https://cityverified.ca/scan",
      changeFrequency: "monthly",
      priority: 0.6,
    },
  ];
}
