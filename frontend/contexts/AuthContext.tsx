"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useSession } from "next-auth/react";

interface AuthUser {
  userId: number | null;
  name: string;
  email: string;
  image: string | null;
  targetRole: string | null;
  isLoading: boolean;
}

const defaultAuth: AuthUser = {
  userId: null,
  name: "Candidate",
  email: "",
  image: null,
  targetRole: null,
  isLoading: true,
};

const AuthContext = createContext<AuthUser>(defaultAuth);

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession();
  const [authUser, setAuthUser] = useState<AuthUser>(defaultAuth);

  useEffect(() => {
    if (status === "loading") {
      setAuthUser((prev) => ({ ...prev, isLoading: true }));
      return;
    }

    if (status === "unauthenticated" || !session?.user) {
      setAuthUser({ ...defaultAuth, isLoading: false });
      return;
    }

    // Session is authenticated — resolve DB user via /auth/me
    async function resolveDbUser() {
      try {
        const res = await fetch("/api/auth/session");
        const sessionData = await res.json();
        // Use the session token to call the backend
        const meRes = await fetch("/api/py/auth/me", {
          headers: {
            // We pass the session cookie — the Next.js rewrite forwards it,
            // but the backend needs the JWT. Use a custom header approach:
            // We embed the user info from the session directly for user resolution.
            "X-Auth-Email": session!.user!.email ?? "",
            "X-Auth-Name": session!.user!.name ?? "",
          },
        });

        if (meRes.ok) {
          const dbUser = await meRes.json();
          setAuthUser({
            userId: dbUser.id,
            name: dbUser.name || session!.user!.name || "User",
            email: dbUser.email || session!.user!.email || "",
            image: session!.user!.image ?? null,
            targetRole: dbUser.target_role ?? null,
            isLoading: false,
          });
        } else {
          // Backend not reachable — use session data with null userId
          setAuthUser({
            userId: null,
            name: session!.user!.name || "User",
            email: session!.user!.email || "",
            image: session!.user!.image ?? null,
            targetRole: null,
            isLoading: false,
          });
        }
      } catch {
        setAuthUser({
          userId: null,
          name: session!.user!.name || "User",
          email: session!.user!.email || "",
          image: session!.user!.image ?? null,
          targetRole: null,
          isLoading: false,
        });
      }
    }

    resolveDbUser();
  }, [session, status]);

  return <AuthContext.Provider value={authUser}>{children}</AuthContext.Provider>;
}
