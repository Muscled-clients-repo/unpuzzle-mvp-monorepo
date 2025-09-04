import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { ThemeProvider } from "@/components/theme-provider"
import { StoreProvider } from "@/components/providers/StoreProvider"
import { SessionProvider } from "@/components/providers/SessionProvider"
import { getServerSession } from "@/lib/auth-server"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Unpuzzle - AI-Powered Learning Platform",
  description: "Accelerate your learning with contextual AI assistance and adaptive content delivery",
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  // Fetch session data on the server
  const session = await getServerSession()
  
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <SessionProvider session={session}>
          <StoreProvider>
            <ThemeProvider
              attribute="class"
              defaultTheme="system"
              enableSystem
              disableTransitionOnChange
            >
              {children}
            </ThemeProvider>
          </StoreProvider>
        </SessionProvider>
      </body>
    </html>
  )
}
