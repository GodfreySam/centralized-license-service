# Centralized License Service - Design & Implementation

To write the code, I had to define how multi-tenancy works in the system. In this case, the "Brand" is the tenant.

## Problem Statement

The goal here is to create a centralized License Service for group.one that acts as the single source of truth for all product entitlements across various brands like WP Rocket and RankMath. This service needs to balance brand-specific isolation with a unified ecosystem view - brands need to be able to provision licenses, and products need to activate them securely, but we also want that ecosystem-wide visibility.

It's a bit of a balancing act: isolation vs centralization, but I think we've got a good approach.

## High-Level Design

The system is built as a multi-tenant service where each Brand acts as a tenant. Pretty straightforward.

Brand Systems connect to the service to manage the lifecycle of licenses - provisioning, renewal, cancellation, all that stuff.

End-User Products (plugins, apps, CLIs) connect to activate usage and check validity. They hit the API to activate and validate.

Admin Access provides a unified view for the group to see all licenses associated with a customer email across the entire ecosystem. This is the "single source of truth" part.

## Data Model (The Single Source of Truth)

To support the requirement that a single license key may unlock multiple licenses, I designed a hierarchical structure:

**Brand**: The top-level entity representing the tenant. Think RankMath, WP Rocket, etc.

**Product**: Specifically tied to a Brand. For example, RankMath owns 'Content AI'. Each product has its own seat limits and whatnot.

**LicenseKey**: A unique identifier provided to the user. It's scoped to a Brand and an email, ensuring a user has one key per brand. This is the "container" that can hold multiple licenses.

**License**: The specific entitlement for a product. Tracks status (valid, suspended, cancelled), expiration, and seat limits. This is where the actual product access is defined.

**Activation**: Represents a "seat" being consumed by a specific instance - like a site URL or host. When someone activates on their WordPress site, that's an activation record.

The hierarchy is: Brand → Product → LicenseKey → License → Activation. Makes sense when you think about it.

## Multi-Tenancy and Isolation

Multi-tenancy is modeled by ensuring all license and product records are associated with a `brand_id`. Simple but effective.

Isolation: Brands can only provision or query licenses for products they own. Brand A should never see Brand B's licenses. Every query gets filtered by the authenticated brand's ID.

Centralization: While brands are isolated, the database is centralized to allow for ecosystem-wide queries. Like listing all licenses for a customer across all brands - that's the admin view (US6).

So we get the best of both worlds: isolation where it matters, but the ability to query across the ecosystem when needed.

## Fulfillment of User Stories

**US1 (Provisioning)**: The service layer ensures that if a user buys an add-on (like Content AI), it gets associated with their existing brand license key rather than creating a new one. The endpoint is `POST /v1/licenses/provision/` - brand provides customer email and product slug, we handle the rest.

**US3 (Activation)**: The system enforces seat limits by checking existing Activation records before allowing a new instance to activate. Validates the key, checks expiration, all that good stuff. Endpoint: `POST /v1/activations/`.

**US4 (Status Check)**: `GET /v1/licenses/{key}/status/` - returns validity, expiration, remaining seats. Pretty straightforward.

**US6 (Ecosystem View)**: A dedicated internal API bypasses brand filters to provide a full list of entitlements by customer email. Endpoint: `GET /v1/customers/{email}/licenses/`. This one requires special authentication since it's admin-only.

## Scaling Plan and Future Extensibility

As the group.one ecosystem grows to millions of activations, we need to think about performance. Here's the plan:

### Caching Strategy (Performance)

Challenge: License status checks (US4) are high-read operations. They can happen every time a WordPress admin page is loaded, which is a lot.

Solution: Implement Redis caching. When a license is checked, store the result in Redis with a TTL (Time-to-Live). Use "Cache Invalidation" to clear the cache only when the license is updated or a new seat is activated. This should cut down on database hits significantly.

### Database Scaling (Volume)

Indexing: Make sure `customer_email`, `license_key`, and `instance_id` are indexed. These are the fields we query most often, so indexes are critical.

Read Replicas: As read traffic (status checks) dwarfs write traffic (provisioning), we can use database read replicas to distribute the load. Most queries are reads anyway.

Archiving: Move cancelled or expired licenses older than 2 years to a "cold storage" table to keep the main production table lean. No need to query old data constantly.

### Webhooks (Extensibility)

Instead of brands constantly polling for status changes, we can implement an Event-Driven Architecture. When a license is suspended in our service, fire a Webhook to the brand's system or the product's update server. This is more efficient than polling and keeps everyone in sync.

## Trade-offs and Decisions

I chose PostgreSQL; a relational DB with strict ACID compliance because license data is highly structured and would require strict ACID compliance for seat limits.

I kept logic out of Django Models and Views using a service layer pattern. This makes the code more testable and allows us to swap API frameworks (e.g., to FastAPI) in the future without rewriting the business logic. The service layer pattern is probably the most important decision here. It keeps things clean and testable.

For multi-tenancy, I chose "Database-level" (filtering by `brand_id`) over "Schema-level" (separate DB schemas per brand). Given the scope of the exercise, this provides sufficient isolation without the dev-ops complexity of managing 50 schemas.

## How to Run Locally

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd centralized-license-service

# Build and run with Docker (Recommended)
docker-compose up --build
```

The Docker setup handles everything - database, migrations, all that.

### API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

These provide interactive interfaces where you can browse all endpoints, see request/response schemas, and test the API directly in your browser.

### Sample Request (US1: Provisioning)

```bash
curl -X POST http://localhost:8000/v1/licenses/provision/ \
     -H "Content-Type: application/json" \
     -H "X-Brand-Name: RankMath" \
     -d '{
           "customer_email": "godfrey@example.com",
           "product_slug": "rankmath-seo"
         }'
```

This creates (or retrieves) a license key for the customer and attaches the product license to it.

### Sample Request (US3: Activation)

```bash
curl -X POST http://localhost:8000/v1/activations/ \
     -H "Content-Type: application/json" \
     -d '{
           "license_key": "YOUR_KEY_HERE",
           "product_slug": "rankmath-seo",
           "instance_id": "https://my-wordpress-site.com"
         }'
```

This activates a seat for the given instance. The system checks seat limits, expiration, all that validation stuff.

## Known Limitations & Next Steps

Authentication: Currently uses a simplified header check (`X-Brand-Name`). Production should use OAuth2 or JWT for brand authentication. The current approach works for a demo but isn't secure enough for production.

Rate Limiting: To prevent API abuse from plugins, we should implement Django-ratelimit. Right now there's nothing stopping someone from hammering the API.

Audit Log: For US5 (History), I would implement django-simple-history to track every change to a license's status for auditing. This wasn't in scope for the initial implementation but it's definitely needed.

Error Handling: We're using standard HTTP status codes (402 for expired, 403 for unauthorized, 429 for seat limit exceeded), but we could make the error responses more detailed with specific error codes and messages.

The middleware logs requests, but we could make the logging more structured (JSON format) for better parsing in production monitoring tools.

## Observability

We've got basic logging in place - middleware logs every API request, especially activation attempts and failures. This helps debug user issues when they come up.

The logging captures:

- Request ID, brand, endpoint, timestamp
- Activation attempts with license key, product, instance ID, and result
- Activation failures with error details, license status, seat limit status, etc.

For production, we'd want to ship these logs to something like CloudWatch or Datadog for better monitoring and alerting.
