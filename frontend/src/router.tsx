import {
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { Layout } from "@/components/Layout";
import { Dashboard } from "@/routes/Dashboard";
import { Upload } from "@/routes/Upload";
import { Jobs } from "@/routes/Jobs";
import { Results } from "@/routes/Results";
import { Detail } from "@/routes/Detail";
import { SettingsPage } from "@/routes/SettingsPage";

const rootRoute = createRootRoute({ component: Layout });

const routes = [
  createRoute({ getParentRoute: () => rootRoute, path: "/", component: Dashboard }),
  createRoute({ getParentRoute: () => rootRoute, path: "/upload", component: Upload }),
  createRoute({ getParentRoute: () => rootRoute, path: "/jobs", component: Jobs }),
  createRoute({ getParentRoute: () => rootRoute, path: "/results", component: Results }),
  createRoute({ getParentRoute: () => rootRoute, path: "/results/$id", component: Detail }),
  createRoute({ getParentRoute: () => rootRoute, path: "/settings", component: SettingsPage }),
];

const routeTree = rootRoute.addChildren(routes);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
