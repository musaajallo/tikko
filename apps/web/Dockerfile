# syntax=docker/dockerfile:1.7
#
# tikko-web image. Multi-stage Next.js standalone build.
#
# Build with:
#   docker build -f apps/web/Dockerfile -t tikko-web .
# The build context must be the monorepo root so workspace packages
# (@tikko/shared-types) are reachable.
FROM node:20-slim AS base

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

# ----------------------------------------------------------------------
# Dependencies — just the lockfile + manifests so this layer caches well.
# ----------------------------------------------------------------------
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/shared-types/package.json ./packages/shared-types/
COPY packages/api-client/package.json ./packages/api-client/
RUN pnpm install --frozen-lockfile

# ----------------------------------------------------------------------
# Build — full sources + next build → .next/standalone.
# ----------------------------------------------------------------------
FROM deps AS build
WORKDIR /app
COPY packages ./packages
COPY apps/web ./apps/web
# Build-time env: the image bakes in the api base URL because Next.js
# inlines NEXT_PUBLIC_* into the client bundle. Override at `docker build`
# time with `--build-arg NEXT_PUBLIC_TIKKO_API_BASE_URL=…`.
ARG NEXT_PUBLIC_TIKKO_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_TIKKO_API_BASE_URL=$NEXT_PUBLIC_TIKKO_API_BASE_URL
RUN pnpm --filter @tikko/web build

# ----------------------------------------------------------------------
# Runtime — tiny image with just the standalone server bundle.
# ----------------------------------------------------------------------
FROM node:20-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Non-root.
RUN groupadd --system --gid 1001 nodejs \
  && useradd --system --uid 1001 --gid nodejs nextjs

# `output: "standalone"` puts a self-contained server bundle here.
COPY --from=build --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public

USER nextjs

EXPOSE 3000

CMD ["node", "apps/web/server.js"]
