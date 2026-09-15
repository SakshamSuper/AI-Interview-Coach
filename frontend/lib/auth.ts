import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";

const hasGoogleOAuthConfig = Boolean(
  process.env.GOOGLE_CLIENT_ID &&
  process.env.GOOGLE_CLIENT_SECRET &&
  !process.env.GOOGLE_CLIENT_ID.includes("your-google-client-id") &&
  process.env.GOOGLE_CLIENT_ID.trim().length > 0
);

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    ...(hasGoogleOAuthConfig
      ? [
          Google({
            clientId: process.env.GOOGLE_CLIENT_ID!,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
          }),
        ]
      : []),
    Credentials({
      id: "google-account",
      name: "Google Account",
      credentials: {
        email: { label: "Email", type: "email" },
        name: { label: "Name", type: "text" },
      },
      async authorize(credentials) {
        const email =
          (credentials?.email as string)?.trim() || "sakshamaggarwal2475@gmail.com";
        const name =
          (credentials?.name as string)?.trim() || "Saksham Aggarwal";
        return {
          id: "1",
          name,
          email,
          image: null,
        };
      },
    }),
  ],
  trustHost: true,
  session: { strategy: "jwt" },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      return true;
    },
    async jwt({ token, user, account, profile }) {
      if (user) {
        token.name = user.name;
        token.email = user.email;
        token.picture = user.image;
      }
      if (account && profile) {
        token.picture = (profile as Record<string, string>).picture ?? token.picture;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        if (token.name) session.user.name = token.name as string;
        if (token.email) session.user.email = token.email as string;
        if (token.picture) session.user.image = token.picture as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  secret:
    process.env.NEXTAUTH_SECRET ||
    process.env.AUTH_SECRET ||
    "c847a9f82d1c5a93e8471b0c95e12847a9f82d1c5a93e8471b0c95e12847a9f8",
});

