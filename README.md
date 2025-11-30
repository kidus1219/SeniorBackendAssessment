# Django Blog Analytics API

This project is a Django REST API that provides analytics for blogs, users, and countries. It focuses on efficient ORM usage, dynamic multi\-table filtering, and time\-series aggregation while avoiding N\+1 queries.

## Features

*   **Blog Views Analytics**: Group and aggregate blog and view counts by country or user.
*   **Top Performers**: Get a Top 10 list of the best-performing blogs, users, or countries based on total views.
*   **Time-Series Performance**: Analyze view trends and growth/decline over time for specific users or all users.
*   **Dynamic Filtering**: A powerful, nested filtering engine that supports `and`, `or`, `not`, and various field operators (`eq`, `in`, `gt`, etc.).
*   **Efficient ORM Usage**: Queries are optimized using `select_related`, `annotate`, `F()` objects, and conditional aggregation to minimize database hits.
*   **Data Seeding**: Includes a command to populate the database with realistic dummy data for immediate testing and demonstration.

## Installation and Setup

Follow these steps to get the project running locally.

1. **Clone the Repository**
    ```bash
    git clone https://github.com/kidus1219/SeniorBackendAssessment.git
    cd SeniorBackendAssessment
    ```

2. **Create and Activate a Virtual Environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Apply Database Migrations**
    This will create the necessary tables in your database(Ensure to have a database named ideeza).
    ```bash
    python manage.py migrate
    ```

5. **Create a Superuser (Optional)**
    ```bash
    python manage.py createsuperuser
    ```

6. **Seed the Database (Recommended)**
    Populate the database with dummy data to test the API endpoints. This command will create countries, users, blogs, and views.
    ```bash
    python manage.py seed_dummy_data
    ```

7. **Run the Development Server**
    ```bash
    python manage.py runserver
    ```
    The API will be available at `http://127.0.0.1:8000/`.

## API Endpoints

All endpoints support common parameters like `start_date`, `end_date`, and the powerful `filter` parameter for dynamic queries.

### 1. Blog Views Analytics

Groups blogs and views by the selected `object_type` within a given time range.

*   **URL**: `/analytics/blog-views/`
*   **Method**: `GET`
*   **Query Parameters**:
    *   `object_type` (string): `user` or `country`. Default: `user`.
    *   `range` (string): `week`, `month`, or `year`. Used if `start_date`/`end_date` are not provided. Default: `year`.
    *   `start_date` (datetime): ISO 8601 format (e.g., `2025-01-01T00:00:00Z`).
    *   `end_date` (datetime): ISO 8601 format. Both start and end dates must be provided or neither(uses range).
    *   `filter_blog_creation` (bool): filter blogs not just blogViews by created_at when true. Default: `false`.
    *   `filter` (string): Dynamic filter string. See guide at the bottom.

*   **Semantics**:
    * `x:` username or country name
    * `y:` number of distinct blogs
    * `z:` total views in [start_date, end_date]


*   **Example Request**:
    ```
    /analytics/blog-views/?object_type=country&range=month
    ```
*   **Example Response**:
    ```json
    {
        "endpoint": "/analytics/blog-views/",
        "object_type": "country",
        "start_date": "...",
        "end_date": "...",
        "labels": "X = Object (User/Country), Y = Total Blogs, Z = Total Views",
        "data": [
            {
                "x": "United States",
                "y": 50,
                "z": 1205
            },
            {
                "x": "Germany",
                "y": 35,
                "z": 987
            }
        ]
    }
    ```

### 2. Top 10 Analytics

Returns the Top 10 blogs, users, or countries based on total views.

*   **URL**: `/analytics/top/`
*   **Method**: `GET`
*   **Query Parameters**:
    *   `top` (string): `user`, `country`, or `blog`. Default: `user`.
    *   `range` (string): `week`, `month`, or `year`. Used if `start_date`/`end_date` are not provided. Default: `year`.
    *   `start_date` (datetime): ISO 8601 format (e.g., `2025-01-01T00:00:00Z`).
    *   `end_date` (datetime): ISO 8601 format. Both start and end dates must be provided or neither(uses range).
    *   `filter_blog_creation` (bool): filter blogs not just blogViews by created_at when true. Default: `false`.
    *   `filter` (string): Dynamic filter string. See guide at the bottom.
*   **Example Request**:
    ```
    /analytics/top/?top=blog&start_date=2025-01-01&end_date=2025-03-31
    ```
*   **Example Response (`top=blog`)**:
    ```json
    {
        "endpoint": "/analytics/top/",
        "top_type": "blog",
        "start_date": "...",
        "end_date": "...",
        "labels": "X = Blog ID, Y = Blog Title, Z = Total Views",
        "data": [
            {
                "x": 152,
                "y": "How to Optimize Django Queries",
                "z": 450
            },
            {
                "x": 88,
                "y": "REST APIs with Python",
                "z": 412
            }
        ]
    }
    ```

### 3. Performance Analytics

Shows time-series performance for a user or all users, including growth/decline percentage compared to the previous period.

*   **URL**: `/analytics/performance/`
*   **Method**: `GET`
*   **Query Parameters**:
    *   `compare` (string): `day`, `week`, `month`, or `year`. The time bucket for aggregation. Default: `month`.
    *   `user` (string): A specific `username` to filter for. If not specified, aggregates for all users.
    *   `filter` (string): Dynamic filter string.
*   **Example Request**:
    ```
    /analytics/performance/?compare=month
    ```
*   **Example Response**:
    ```json
    {
        "compare": "month",
        "start_date": "...",
        "end_date": "...",
        "labels": "X = Period & Blogs Created, Y = Total Views, Z = Growth %",
        "data": [
            {
                "x": "Jan 2025 (5 Blogs)",
                "y": 150,
                "z": "N/A"
            },
            {
                "x": "Feb 2025 (8 Blogs)",
                "y": 225,
                "z": "+50.0%"
            },
            {
                "x": "Mar 2025 (3 Blogs)",
                "y": 180,
                "z": "-20.0%"
            }
        ]
    }
    ```

## Dynamic Filtering Guide

The `filter` query parameter accepts a URL-encoded string that is parsed into a Django `Q` object. This allows for complex, nested queries on the `Blog` model.

#### Syntax

*   **Basic Condition**: `field:operator:value`
*   **Logical Operators**: `and(...)`, `or(...)`, `not(...)`
*   **Combining**: Conditions inside logical operators are comma-separated.

#### Supported Operators

| Operator | Description          | Example                      |
| :------- | :------------------- | :--------------------------- |
| `eq`     | Equals               | `author__username:eq:kidus1219` |
| `ne`     | Not Equals           | `author__country__code:ne:US` |
| `gt`     | Greater Than         | `id:gt:100`                  |
| `gte`    | Greater Than or Equal| `created_at:gte:2025-01-01`   |
| `lt`     | Less Than            | `id:lt:50`                   |
| `lte`    | Less Than or Equal   | `created_at:lte:2025-03-31`   |
| `in`     | In a list (pipe-separated) | `author__username:in:user1|user2` |

#### Examples

1.  **Simple AND**: Find blogs by `kidus1219` with an ID greater than 10.
    *   **Filter String**: `and(author__username:eq:kidus1219,id:gt:10)`
    *   **URL**: `?filter=and(author__username:eq:kidus1219,id:gt:10)`

2.  **OR with IN**: Find blogs where the author is `user1` or `user2`.
    *   **Filter String**: `author__username:in:user1|user2`
    *   **URL**: `?filter=author__username:in:user1|user2`

3.  **Complex Nested Query**: Find blogs from country `US` that are NOT by `testuser`, OR blogs with a title containing "Django".
    *   **Filter String**: `or(and(author__country__code:eq:US,not(author__username:eq:testuser)),title__icontains:eq:Django)`
    *   **URL (URL-Encoded)**: `?filter=or(and(author__country__code:eq:US,not(author__username:eq:testuser)),title__icontains:eq:Django)`
    *(Note: The parser supports any valid Django field lookup like `title__icontains` passed in the `field` part of the condition)*.