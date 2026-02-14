# Cerebro CLI Command Reference

## Core Commands

- [cerebro info](cerebro_info.md) — Display environment and system information
- [cerebro version](cerebro_version.md) — Display the current version

## Knowledge Commands

- [cerebro knowledge analyze](cerebro_knowledge_analyze.md) — Extract AST and generate JSONL artifacts
- [cerebro knowledge batch-analyze](cerebro_knowledge_batch-analyze.md) — Process all repositories from config file
- [cerebro knowledge summarize](cerebro_knowledge_summarize.md) — Create local vector database (ChromaDB)

## Operations Commands

- [cerebro ops health](cerebro_ops_health.md) — Check system health (credentials, permissions, APIs)

## RAG Commands

- [cerebro rag query](cerebro_rag_query.md) — Query the local RAG engine with precision metrics

## Metrics Commands

- `cerebro metrics scan` — Full zero-token scan of all repositories
- `cerebro metrics watch` — Interactive real-time repository watcher
- `cerebro metrics report` — Detailed metrics report for a single repository

## GCP Commands

- `cerebro gcp status` — Check GCP SDK and authentication status
- `cerebro gcp create-engine` — Create a new Discovery Engine search engine
- `cerebro gcp burn` — Execute batch queries for credit utilization
- `cerebro gcp monitor` — Monitor GCP credit usage in real-time

## Strategy Commands

- `cerebro strategy optimize` — Optimize career strategy based on ROI analysis
- `cerebro strategy salary` — Gather salary intelligence for target role
- `cerebro strategy moat` — Build personal competitive moat analysis
- `cerebro strategy trends` — Predict career and technology trends

## Content Commands

- `cerebro content mine` — Mine valuable content from various sources
- `cerebro content analyze` — Analyze a single content file in detail

## Test Commands

- `cerebro test grounded-search` — Test grounded search API functionality
- `cerebro test grounded-gen` — Test grounded generation API
- `cerebro test verify-api` — Verify grounded API endpoints
