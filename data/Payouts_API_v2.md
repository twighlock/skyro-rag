# Payouts API v2 (Human-Readable)
**Base URL:** `/api/v2`

## Create Batch Payouts
**POST** `/payouts/batch`  
**Body:**

{
  "items": [
    { "account": "US123", "amount": 100, "currency": "USD" },
    { "account": "EU456", "amount": 90, "currency": "EUR" }
  ],
  "callback": "https://example.com/hook"
}
{ "batch_id": "bat_9f3...", "accepted": 2 }
