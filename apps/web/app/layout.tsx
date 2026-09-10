import "./globals.css";

export const metadata = {
  title: "X.page — business identity for AI agents",
  description: "Businesses are invisible to AI agents. X.page scores the gap and hosts a verified page an agent can cite."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
