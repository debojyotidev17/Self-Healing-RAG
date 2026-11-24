# AcroCorp Cloud Engine Specification

## Overview
AcroCorp Cloud Engine (ACE) is a serverless platform designed for event-driven compute workloads. ACE automatically scales execution environments based on incoming HTTP request volume and event bus streams.

## Authentication & Authorization
All API requests to ACE must include a Bearer Token in the `Authorization` header:
`Authorization: Bearer <ACE_API_KEY>`

Tokens expire after 90 days. Service accounts can generate long-lived tokens with custom IAM permissions through the AcroCorp Admin Portal.

## Deployment Regions
AcroCorp Cloud Engine currently supports three primary deployment regions:
- `us-east-1` (N. Virginia, USA)
- `eu-central-1` (Frankfurt, Germany)
- `ap-southeast-1` (Singapore)

Workloads deployed to `us-east-1` support auto-failover to `us-west-2` in the event of an availability zone outage.

## API Rate Limits & Quotas
- **Free Tier**: 1,000 requests per minute per IP. Maximum function execution timeout is 30 seconds.
- **Pro Tier**: 10,000 requests per minute per tenant. Maximum function execution timeout is 300 seconds (5 minutes).
- **Enterprise Tier**: 100,000 requests per minute per tenant with custom execution timeouts up to 30 minutes.

## Pricing Tiers
- **Free Tier**: $0/month up to 100,000 execution GB-seconds.
- **Pro Tier**: $49/month plus $0.00001667 per execution GB-second beyond the monthly 500,000 free execution units.
- **Enterprise Tier**: Custom pricing with dedicated VPC peering, single-tenant clusters, and 99.99% uptime SLA.
