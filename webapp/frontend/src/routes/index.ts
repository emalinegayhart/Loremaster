import { RootRoute, Route, Router } from '@tanstack/react-router';
import { createProtectedRouteGuard, createPublicRouteGuard } from '../lib/routeGuards';
import { RootLayout } from './RootLayout';
import { HomePage } from '../pages/HomePage';
import { LoginPage } from '../pages/LoginPage';
import { AuthCallbackPage } from '../pages/AuthCallbackPage';
import { EditorPage } from '../pages/EditorPage';
import { BotPage } from '../pages/BotPage';
import { NotFoundPage } from '../pages/NotFoundPage';

/**
 * Root route - parent of all other routes
 * Renders RootLayout which includes Header and Outlet for child routes
 */
const rootRoute = new RootRoute({
  component: RootLayout,
});

/**
 * Home route (/)
 * Public route showing home page
 */
const homeRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,
});

/**
 * Login route (/login)
 * Public route with publicGuard - redirects to /editor if already authenticated
 * Supports optional redirect search param for post-login navigation
 */
const loginRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
  beforeLoad: createPublicRouteGuard(),
  validateSearch: (search: Record<string, unknown>) => ({
    redirect: (search.redirect as string) ?? undefined,
  }),
});

/**
 * Auth callback route (/auth/callback)
 * Public route that handles OAuth callback
 * Backend handles authentication, this page verifies and redirects
 */
const authCallbackRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/auth/callback',
  component: AuthCallbackPage,
});

/**
 * Editor route (/editor)
 * Protected route with protectedGuard - redirects to /login if not authenticated
 * Preserves current location in search params for post-login redirect
 */
const editorRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/editor',
  component: EditorPage,
  beforeLoad: createProtectedRouteGuard(),
});

/**
 * Bot public view route (/$slug)
 * Dynamic route for viewing published bots by slug
 * Example: /my-awesome-bot
 */
const botRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/$slug',
  component: BotPage,
  validateSearch: (search: Record<string, unknown>) => ({
    // Can add search params here for bot view if needed
  }),
});

/**
 * Not found route (catch-all)
 * Matches any undefined route and displays 404 page
 */
const notFoundRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '*',
  component: NotFoundPage,
});

/**
 * Route tree - defines all routes in the application
 * Structure:
 * - / (home)
 * - /login (public, auto-redirects if authed)
 * - /auth/callback (oauth callback)
 * - /editor (protected)
 * - /$slug (dynamic bot view)
 * - /* (404 catch-all)
 */
const routeTree = rootRoute.addChildren([
  homeRoute,
  loginRoute,
  authCallbackRoute,
  editorRoute,
  botRoute,
  notFoundRoute,
]);

/**
 * Router instance
 * Exported for use in main.tsx with RouterProvider
 */
export const router = new Router({
  routeTree,
  defaultPreload: 'intent',
  defaultPreloadDelay: 50,
});

/**
 * Register router for type safety in components
 * This ensures useRouter() calls have proper types
 */
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
