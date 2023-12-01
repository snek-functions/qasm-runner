# Stage 1: Build stage with Bun image
FROM oven/bun:1 as base

LABEL description="This container serves as an entry point for our future Snek Function projects."
LABEL org.opencontainers.image.source="https://github.com/cronitio/pylon-template"
LABEL maintainer="opensource@cronit.io"

WORKDIR /usr/src/pylon

# Install dependencies into the temp directory
# This will cache them and speed up future builds
FROM base AS install
RUN mkdir -p /temp/dev
COPY package.json bun.lockb /temp/dev/
RUN cd /temp/dev && bun install --frozen-lockfile

# Install with --production (exclude devDependencies)
RUN mkdir -p /temp/prod
COPY package.json bun.lockb /temp/prod/
RUN cd /temp/prod && bun install --frozen-lockfile --production

# Copy node_modules from the temp directory
# Then copy all (non-ignored) project files into the image
FROM install AS prerelease
COPY --from=install /temp/dev/node_modules node_modules
COPY . .

# [optional] Tests & build
ENV NODE_ENV=production
# RUN bun test
RUN bun run pylon build

# Stage 2: Add Python to the image
FROM python:3.9-slim AS python

# Set working directory
WORKDIR /usr/src/pylon

# Copy Python-specific files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Final stage
FROM base AS release

# Copy production dependencies and source code into the final image
COPY --from=install /temp/prod/node_modules node_modules
COPY --from=prerelease /usr/src/pylon/.pylon/index.js .pylon/index.js
COPY --from=prerelease /usr/src/pylon/package.json .

# Copy Python dependencies
COPY --from=python /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Install python 3.9 in the release image
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.9 \
    python3-setuptools \
    python3-wheel \
    && rm -rf /var/lib/apt/lists/*

# Run the app
USER bun
EXPOSE 3000/tcp
ENTRYPOINT ["bun", "run", "pylon-server"]
