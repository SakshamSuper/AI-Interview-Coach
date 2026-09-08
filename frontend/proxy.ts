export { auth as proxy } from "@/lib/auth";

export const config = {
  // Protect all routes except: login page, NextAuth callbacks, static assets, API routes
  matcher: [
    "/((?!login|api/auth|_next/static|_next/image|favicon.ico|.*\\.png|.*\\.svg).*)",
  ],
};
