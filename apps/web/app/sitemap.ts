import type { MetadataRoute } from "next";

const CANONICAL_ORIGIN = "https://www.cityverified.ca";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${CANONICAL_ORIGIN}/`,
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${CANONICAL_ORIGIN}/scan`,
      changeFrequency: "monthly",
      priority: 0.6,
    },
  ];
}
