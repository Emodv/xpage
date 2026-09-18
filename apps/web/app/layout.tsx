import "./globals.css";

export const metadata = {
  metadataBase: new URL("https://cityverified.ca"),
  title: "CityVerified — Trusted Local Business Infrastructure",
  description: "CityVerified helps AI agents and people discover local businesses using structured service, location, provenance, verification, and freshness signals.",
  alternates: {
    canonical: "/"
  },
  robots: {
    index: true,
    follow: true
  },
  openGraph: {
    title: "CityVerified — Trusted Local Business Infrastructure",
    description: "Structured local-business discovery for AI agents and people.",
    url: "https://cityverified.ca",
    siteName: "CityVerified.ca",
    type: "website"
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
