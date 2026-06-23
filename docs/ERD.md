# Entity-Relationship Diagram

```mermaid
erDiagram
  USER ||--o| PHARMACY : "is (PHARMACY role)"
  USER ||--o| DISTRIBUTOR : "is (DISTRIBUTOR role)"
  DISTRIBUTOR ||--o{ OFFER : carries
  MEDICATION ||--o{ OFFER : "is offered as"
  PHARMACY ||--o{ ORDER : places
  DISTRIBUTOR ||--o{ ORDER : fulfills
  ORDER ||--o{ ORDER_ITEM : has
  ORDER ||--o{ ORDER_EVENT : "audit-logged by"
  USER ||--o{ CHAT_SESSION : owns
  CHAT_SESSION ||--o{ CHAT_MESSAGE : contains

  USER {
    int id PK
    string email UK
    string hashed_password
    string role
    string full_name
    bool is_active
    bool is_suspended
  }
  PHARMACY {
    int id PK
    int user_id FK
    string name
    string license_number UK
    string address
    string phone
  }
  DISTRIBUTOR {
    int id PK
    int user_id FK
    string company_name
    string license_number UK
    int accepted_orders_count
    int rejected_orders_count
  }
  MEDICATION {
    int id PK
    string name
    string active_ingredient
    string atc_code
    string form
    string strength
    string manufacturer
  }
  OFFER {
    int id PK
    int distributor_id FK
    int medication_id FK
    float unit_price
    float discount_percent
    int stock
  }
  ORDER {
    int id PK
    int pharmacy_id FK
    int distributor_id FK
    string status
    float total_amount
  }
  ORDER_ITEM {
    int id PK
    int order_id FK
    int medication_id FK
    int quantity
    float unit_price
    float discount_percent
  }
  ORDER_EVENT {
    int id PK
    int order_id FK
    int actor_user_id FK
    string from_status
    string to_status
    string note
    datetime created_at
  }
```

## Why this shape

- **One `User` table, two profile tables.** A user has exactly one role, and
  the role determines which profile (Pharmacy / Distributor) is attached.
  Admins have no profile. Keeping profiles in their own tables means
  pharmacy-specific or distributor-specific columns never bloat the user
  table.
- **`Medication` is global, `Offer` is per-distributor.** This is what
  enables the comparison feature: search a medication once, join through
  `Offer` to see every distributor that carries it.
- **`OrderItem` snapshots pricing.** We copy `unit_price` and
  `discount_percent` onto the item at creation time. A distributor changing
  their prices tomorrow must not retroactively change yesterday's order
  totals.
- **`OrderEvent` is append-only.** Every state transition writes a row; we
  never update or delete events. This gives us a complete audit trail of
  who did what to which order and when - the foundation of defendable
  "order tracking".
- **No multi-distributor orders.** An `Order` belongs to exactly one
  distributor. A pharmacy that wants medications from two distributors
  places two orders. Far simpler than partitioning a single cart and
  matches how every B2B catalog works in practice.
