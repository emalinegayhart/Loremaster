import { redirect } from '@tanstack/react-router';
import type { BeforeLoadContext } from '@tanstack/react-router';

/**
 * Protected route guard: Checks if user is authenticated
 * Redirects to /login if not, preserving the current location for post-login redirect
 * 
 * Usage:
 * ```ts
 * beforeLoad: createProtectedRouteGuard()
 * ```
 */
export function createProtectedRouteGuard() {
  return async (ctx: BeforeLoadContext) => {
    // Import here to avoid circular dependencies
    const { useAuth } = await import('../hooks/useAuth');
    
    // Note: This is a limitation of beforeLoad - it can't use hooks directly
    // We'll check the token from localStorage as a workaround for now
    // In a real app, you'd use a separate context or store that checks on app load
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      // Preserve the current location for post-login redirect
      throw redirect({
        to: '/login',
        search: {
          redirect: ctx.location.pathname + ctx.location.search,
        },
      });
    }
  };
}

/**
 * Public route guard: Redirects to /editor if user is already authenticated
 * Useful for login pages to prevent authenticated users from accessing them
 * 
 * Usage:
 * ```ts
 * beforeLoad: createPublicRouteGuard()
 * ```
 */
export function createPublicRouteGuard() {
  return async (ctx: BeforeLoadContext) => {
    const token = localStorage.getItem('auth_token');
    
    if (token) {
      // User is already authenticated, redirect to editor
      throw redirect({
        to: '/editor',
      });
    }
  };
}
