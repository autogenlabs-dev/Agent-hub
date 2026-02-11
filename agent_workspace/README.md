# Simple Node.js REST API

A basic REST API built with Express.js.

## Features

- GET / - API info and available endpoints
- GET /health - Health check endpoint
- GET /items - Retrieve all items
- GET /items/:id - Retrieve a specific item
- POST /items - Create a new item
- PUT /items/:id - Update an existing item
- DELETE /items/:id - Delete an item

## Installation

```bash
npm install
```

## Running

```bash
# Production
npm start

# Development (with auto-reload)
npm dev
```

## API Usage Examples

### Get all items
```bash
curl http://localhost:3000/items
```

### Get specific item
```bash
curl http://localhost:3000/items/1
```

### Create new item
```bash
curl -X POST http://localhost:3000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "New Item", "description": "A new item"}'
```

### Update item
```bash
curl -X PUT http://localhost:3000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

### Delete item
```bash
curl -X DELETE http://localhost:3000/items/1
```

## Notes

- Data is stored in-memory and resets on server restart
- Default port is 3000 (configurable via PORT environment variable)
