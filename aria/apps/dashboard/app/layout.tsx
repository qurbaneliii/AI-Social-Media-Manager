import "./globals.css";
import { ReactNode } from "react";
import { Nav } from "../components/nav";
import { Providers } from "./providers";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body min-h-screen">
        <Providers>
          <main className="mx-auto max-w-6xl p-6 md:p-10">
            <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h1 className="font-display text-4xl">ARIA Dashboard</h1>
                <p className="text-muted">Automated Reach & Intelligence Architect</p>
              </div>
              <Nav />
            </header>
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
