# ZPages

ZPages are custom debug dashboards you can add to your service. Build pages with tables, containers, and other components that render as HTML or JSON.

## Quick Start

```python
from hawk.zpages import ZPage, add_page
from hawk.zpages.components import ZTable, ZContainer

# Create a page
page = ZPage("Service Status", description="Current service state")

# Add components
page.add(ZTable(
    cols=["Metric", "Value"],
    rows=[
        ["Uptime", "3d 14h"],
        ["Requests", "1.2M"],
        ["Errors", "42"],
    ]
))

# Register at /debug/status/
add_page("status", page)
```

Access at `GET /debug/status/` (HTML) or `GET /debug/status/?format=json` (JSON).

## Components

### ZTable

Display data in a table:

```python
from hawk.zpages.components import ZTable, TableStyle

# Basic table
table = ZTable(
    cols=["Name", "Status", "Latency"],
    rows=[
        ["API", "healthy", "12ms"],
        ["DB", "healthy", "3ms"],
    ]
)

# Styled table
table = ZTable(
    cols=["Setting", "Value"],
    rows=[["Debug", "true"], ["Log Level", "info"]],
    style=TableStyle.PROPERTY,  # or TableStyle.STRIPPED
)
```

### ZContainer

Group components together:

```python
from hawk.zpages.components import ZContainer

container = ZContainer(id="metrics")
container.add(ZTable(...))
container.add(ZTable(...))

page.add(container)
```

Or use the fluent API:

```python
with page.container() as section:
    section.add(ZTable(...))
```

## Page Options

```python
page = ZPage(
    "Dashboard",
    description="Service overview",      # Shown in header
    theme_color=ThemeColor.BLUE,         # Page accent color
)

# Auto-refresh (seconds)
page.auto_refresh = 30
```

## Output Formats

```bash
# HTML (default) - human-readable dashboard
curl "http://localhost:8000/debug/mypage/"

# JSON - for scripts and automation
curl "http://localhost:8000/debug/mypage/?format=json"

# With auto-refresh
curl "http://localhost:8000/debug/mypage/?refresh=10"
```

## Registry API

```python
from hawk.zpages import add_page, get_page, get_pages, get_page_routes

# Register a page
add_page("health", health_page)

# Get a specific page
page = get_page("health")

# List all routes
routes = get_page_routes()  # ["health", "status", "vars", ...]

# Get all pages
pages = get_pages()  # {"health": ZPage, ...}
```

## Reserved Routes

Routes starting with `/prof/` are reserved for profiling endpoints and cannot be used for custom pages.
