# heuristpy

`heuristpy` is a Python client for [Heurist](https://heuristnetwork.org/)
databases with a session-oriented API. It mirrors the functionality of the
[heuristR](https://github.com/Center-for-Archaeology-and-Society/heuristR)
package for R.

## Overview

`heuristpy` provides a practical Python interface for working with Heurist
databases from scripts, analysis workflows, and repeatable data-management
tasks. It is designed to make authentication, metadata inspection, record
retrieval, and safe scripted updates easier to manage from Python.

The package is especially useful when you want to move beyond manual work in
the Heurist web interface and begin building reproducible Python workflows for:

- metadata inspection and schema exploration
- record retrieval for analysis or reporting
- controlled creation of new records
- safer scripted updates that avoid destructive partial saves
- reversible data maintenance with rollback support

## What Is Heurist?

[Heurist](https://heuristnetwork.org/) is a web-based database platform built
for research projects that need flexible, relational data structures without a
custom application build.

For hosted use, the public Huma-Num server provides a database creation flow
at [heurist.huma-num.fr/heurist/startup/](https://heurist.huma-num.fr/heurist/startup/).

## Installation

Install from source:

```bash
pip install .
```

Or install in development mode with test dependencies:

```bash
pip install -e ".[dev]"
```

## Authentication and Sessions

`heuristpy` separates session creation from login:

1. `heurist_session()` creates a client object with the base URL, database
   name, and timeout.
2. `heurist_login()` uses that client to authenticate and retain the returned
   session cookies.

```python
from heuristpy import heurist_session, heurist_login

session = heurist_session(
    base_url="https://heurist.huma-num.fr/heurist",
    database="my_database",
)
session = heurist_login(
    session,
    username="my_username",
    password="my_password",
)
```

## Basic Workflow

```python
from heuristpy import (
    heurist_session,
    heurist_login,
    heurist_rectypes,
    heurist_get_record,
)

session = heurist_session(
    base_url="https://heurist.huma-num.fr/heurist",
    database="my_database",
)
session = heurist_login(session, username="user", password="pass")

rectypes = heurist_rectypes(session)
record = heurist_get_record(session, 3)
```

## Inspect Database Structure

```python
from heuristpy import heurist_rectypes, heurist_fields, heurist_structure

rectypes = heurist_rectypes(session)
fields = heurist_fields(session)
structure = heurist_structure(session)
```

## Read Records

Fetch a single record:

```python
from heuristpy import heurist_get_record

record = heurist_get_record(session, 3)
```

Search for records using Heurist query syntax:

```python
from heuristpy import heurist_find_records

sites = heurist_find_records(session, q="t:Site sortby:-m")
```

Low-level access:

```python
from heuristpy import heurist_raw_record_output

raw = heurist_raw_record_output(session, query={"q": "t:Site", "format": "json"})
```

## Create Records

```python
from heuristpy import heurist_create_record

change = heurist_create_record(
    session,
    rectype_id=10,
    details={"1": {"0": "North Ridge Wash"}},
)
new_record_id = change.record_id
```

## Update Records Safely

`heurist_patch_record()` performs a safe read-modify-write update:

```python
from heuristpy import heurist_patch_record

change = heurist_patch_record(
    session,
    record_id=42,
    details={"1": {"0": "Updated Site Title"}},
    mode="replace",
)
```

## Rollback

Each write helper returns a `HeuristChange` object that can be rolled back:

```python
from heuristpy import heurist_rollback

heurist_rollback(change)
```

## Link Related Records

```python
from heuristpy import heurist_link_record

change = heurist_link_record(
    session,
    source_record_id=108,
    detail_type_id=1108,
    target_record_id=42,
)
```

## Schema Creation Helpers

```python
from heuristpy import (
    heurist_create_vocabulary_group,
    heurist_create_vocabulary,
    heurist_create_term,
    heurist_create_rectype,
    heurist_create_detail_type,
    heurist_attach_detail_type,
)
```

## Low-Level Endpoint Access

```python
from heuristpy import (
    heurist_raw_record_output,
    heurist_raw_record_edit,
    heurist_raw_entity,
    heurist_raw_entity_edit,
)

raw_read = heurist_raw_record_output(session, query={"q": "t:Site"})
raw_meta = heurist_raw_entity(session, action="structure", entity="all")
```

## Local Configuration

For local development, create a `.env` file (do not commit credentials):

```
HEURISTPY_TEST_BASE_URL=https://your-heurist-host.example/heurist
HEURISTPY_TEST_DB=your_database_name
HEURIST_USERNAME=your_username
HEURIST_PASSWORD=your_password
```

## Running Tests

```bash
pytest
```

## License

MIT — see [LICENSE](LICENSE).
