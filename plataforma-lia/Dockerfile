FROM node:22-alpine AS base

FROM base AS builder
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_WS_URL
ARG NEXT_PUBLIC_TEAMS_URL
ARG NEXT_PUBLIC_WHATSAPP_NUMBER

# WorkOS/Jira need env vars at build time for API route collection
ENV WORKOS_API_KEY=build_placeholder
ENV WORKOS_CLIENT_ID=build_placeholder
ENV WORKOS_SESSION_SECRET=build_placeholder_secret_at_least_32_chars_long
ENV JIRA_HOST=https://placeholder.atlassian.net
ENV JIRA_EMAIL=placeholder@example.com
ENV JIRA_API_TOKEN=placeholder

ENV NODE_OPTIONS=--max-old-space-size=3072
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
