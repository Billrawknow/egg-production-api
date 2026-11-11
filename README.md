# Egg Production API

A REST API for a poultry farmer in Kiambu with three sheds (A, B and C). Each day he logs how many eggs each shed produced. At the end of the week, one request returns every record with a running total and the total per shed. It replaces sending himself numbers on WhatsApp and adding them up by hand on Saturday.

AI Masterclass 2, Week 4, Day 17: building a REST API.

## Pricing

- **Build and deploy:** KES 15,000 one-off. That covers building the API, putting it online and showing him how to log eggs from his phone.
- **Monthly:** KES 2,000. That covers hosting, daily backups, fixes and small changes.

## Endpoints

### `POST /api/eggs`: log a day's count for one shed

```json
{"shed": "A", "date": "2026-11-09", "count": 412}
```

Returns **201 Created** with the saved record:
```json
{"id": 1, "shed": "A", "date": "2026-11-09", "count": 412}
```

| Problem | Status | Message |
|---|---|---|
| Missing `shed`, `date` or `count` | 400 | Lists the missing field(s) |
| Shed isn't A, B or C | 400 | "Unknown shed 'D'. Use one of: A, B, C" |
| Date not in `YYYY-MM-DD` format, or in the future | 400 | Explains the format |
| Count isn't a whole number from 0 to 5,000 | 400 | Explains what's allowed |
| That shed already has a record for that date | 409 Conflict | Prevents counting the same day twice |

The shed can be sent as `"A"`, `"a"` or `"Shed A"`.

### `GET /api/eggs`: all records with running totals

Records are sorted oldest first. Each one has a `running_total`, and the response ends with totals per shed and for the whole farm.

Optional filters:
- `?shed=A`: one shed only
- `?from=2026-11-09&to=2026-11-15`: one week

```json
{
  "records": [
    {"id": 1, "shed": "A", "date": "2026-11-09", "count": 412, "running_total": 412},
    {"id": 2, "shed": "B", "date": "2026-11-09", "count": 388, "running_total": 800},
    {"id": 3, "shed": "A", "date": "2026-11-10", "count": 405, "running_total": 1205},
    {"id": 4, "shed": "B", "date": "2026-11-10", "count": 396, "running_total": 1601}
  ],
  "totals": {"by_shed": {"A": 817, "B": 784, "C": 0}, "all_sheds": 1601, "records": 4}
}
```

## Setup and run

```bash
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000/api/eggs`.

## Testing with curl

With the server running, open a **second terminal** in this folder and run the test script. It sends 4 valid records across two sheds, then 5 requests that should be rejected, then the GET requests:
```bash
bash test_requests.sh
```

Or send requests yourself:
```bash
curl -X POST http://127.0.0.1:5000/api/eggs \
  -H "Content-Type: application/json" \
  -d '{"shed": "A", "date": "2026-11-09", "count": 412}'

curl http://127.0.0.1:5000/api/eggs
curl "http://127.0.0.1:5000/api/eggs?from=2026-11-09&to=2026-11-15"
```

## Optional API key

To stop anyone with the URL from reading or adding records, create a `.env` file:
```
EGG_API_KEY=a-long-random-string
```
Every request must then send the header `X-API-Key: a-long-random-string`, or it gets **401 Unauthorized**. To run the test script with a key:
```bash
API_KEY=a-long-random-string bash test_requests.sh
```

## Limitations of this version

- **Data is held in memory,** so it's lost when the server restarts. A real deployment for the farmer would save records to a database (e.g. SQLite).
- Records can't be edited or deleted yet. A `PUT /api/eggs/<id>` endpoint would be the next step for correcting mistakes.
- IDs come from a counter, not `len(records) + 1`, so they stay unique even after deletes are added.
