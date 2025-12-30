# VRCX Database Structure Review

## Overview

VRCX uses **SQLite** as its primary database for storing VRChat-related data. The database stores information about locations, users, friends, notifications, avatars, worlds, and game logs collected while the application runs.

**Database Location:** `%APPDATA%\VRCX\VRCX.sqlite3` (Windows) or user-configurable via `VRCX_DatabaseLocation`

---

## Database Architecture

### Connection Details (Dotnet/SQLite.cs)

- **Type:** SQLite 3
- **Connection String:** `Data Source="[path]";Version=3;PRAGMA locking_mode=NORMAL;PRAGMA busy_timeout=5000;PRAGMA journal_mode=WAL;PRAGMA optimize=0x10002;`
- **Key Pragmas:**
    - `journal_mode=WAL`: Write-Ahead Logging for better concurrency
    - `busy_timeout=5000`: 5-second timeout for locked database
    - `optimize=0x10002`: Query optimization

---

## Table Schema

### User-Specific Tables (Prefix: User ID with dashes/underscores removed)

**Note:** These tables are dynamically created per user. Table names use a sanitized user ID prefix (e.g., if user ID is `usr-123-abc`, prefix becomes `usr123abc`)

#### 1. `{userPrefix}_feed_gps`

**Purpose:** Track friend location changes

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_feed_gps (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    user_id TEXT,
    display_name TEXT,
    location TEXT,
    world_name TEXT,
    previous_location TEXT,
    time INTEGER,
    group_name TEXT
)
```

- **Tracks:** When friends change locations/instances
- **Key Fields:** `created_at` (ISO timestamp), `location` (instance), `world_name`, `time` (duration in that location?)

#### 2. `{userPrefix}_feed_status`

**Purpose:** Track friend status changes

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_feed_status (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    user_id TEXT,
    display_name TEXT,
    status TEXT,
    status_description TEXT,
    previous_status TEXT,
    previous_status_description TEXT
)
```

- **Tracks:** Friend online/offline/busy status changes
- **Status Values:** (Check VRChat API for exact values)

#### 3. `{userPrefix}_feed_bio`

**Purpose:** Track friend bio/description changes

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_feed_bio (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    user_id TEXT,
    display_name TEXT,
    bio TEXT,
    previous_bio TEXT
)
```

#### 4. `{userPrefix}_feed_avatar`

**Purpose:** Track friend avatar changes

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_feed_avatar (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    user_id TEXT,
    display_name TEXT,
    owner_id TEXT,
    avatar_name TEXT,
    current_avatar_image_url TEXT,
    current_avatar_thumbnail_image_url TEXT,
    previous_current_avatar_image_url TEXT,
    previous_current_avatar_thumbnail_image_url TEXT
)
```

#### 5. `{userPrefix}_feed_online_offline`

**Purpose:** Track friend online/offline events

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_feed_online_offline (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    user_id TEXT,
    display_name TEXT,
    type TEXT,        -- 'online' or 'offline'
    location TEXT,
    world_name TEXT,
    time INTEGER,
    group_name TEXT
)
```

#### 6. `{userPrefix}_friend_log_current`

**Purpose:** Current snapshot of friends list

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_friend_log_current (
    user_id TEXT PRIMARY KEY,
    display_name TEXT,
    trust_level TEXT,
    friend_number INTEGER
)
```

- **Single Row Per Friend:** Stores current state

#### 7. `{userPrefix}_friend_log_history`

**Purpose:** Historical log of friend list changes

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_friend_log_history (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    type TEXT,        -- 'added' or 'removed'
    user_id TEXT,
    display_name TEXT,
    previous_display_name TEXT,
    trust_level TEXT,
    previous_trust_level TEXT,
    friend_number INTEGER
)
```

- **Tracks:** Friend additions/removals and trust level changes

#### 8. `{userPrefix}_notifications`

**Purpose:** Store received notifications

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_notifications (
    id TEXT PRIMARY KEY,
    created_at TEXT,
    type TEXT,             -- Notification type
    sender_user_id TEXT,
    sender_username TEXT,
    receiver_user_id TEXT,
    message TEXT,
    world_id TEXT,
    world_name TEXT,
    image_url TEXT,
    invite_message TEXT,
    request_message TEXT,
    response_message TEXT,
    expired INTEGER
)
```

#### 9. `{userPrefix}_moderation`

**Purpose:** Track blocked/muted users

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_moderation (
    user_id TEXT PRIMARY KEY,
    updated_at TEXT,
    display_name TEXT,
    block INTEGER,     -- 0 or 1
    mute INTEGER       -- 0 or 1
)
```

#### 10. `{userPrefix}_avatar_history`

**Purpose:** Track your avatar changes

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_avatar_history (
    avatar_id TEXT PRIMARY KEY,
    created_at TEXT,
    time INTEGER
)
```

#### 11. `{userPrefix}_notes`

**Purpose:** User memos/notes

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_notes (
    user_id TEXT PRIMARY KEY,
    display_name TEXT,
    note TEXT,
    created_at TEXT
)
```

#### 12. `{userPrefix}_mutual_graph_friends`

**Purpose:** Graph analysis - mutual friends

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_mutual_graph_friends (
    friend_id TEXT PRIMARY KEY
)
```

#### 13. `{userPrefix}_mutual_graph_links`

**Purpose:** Graph analysis - mutual friend connections

```sql
CREATE TABLE IF NOT EXISTS {userPrefix}_mutual_graph_links (
    friend_id TEXT NOT NULL,
    mutual_id TEXT NOT NULL,
    PRIMARY KEY(friend_id, mutual_id)
)
```

---

### Global Tables (Shared across all users)

#### 1. `gamelog_location`

**Purpose:** Your own location/instance changes - **CRITICAL FOR YOUR USE CASE**

```sql
CREATE TABLE IF NOT EXISTS gamelog_location (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    location TEXT,     -- Instance ID (e.g., "wrld_12345:12345~region(us)")
    world_id TEXT,
    world_name TEXT,
    time INTEGER,      -- Duration in seconds at this location
    group_name TEXT,
    UNIQUE(created_at, location)
)
```

✅ **KEY TABLE:** Use this to track when you were in each instance and for how long

#### 2. `gamelog_join_leave`

**Purpose:** User join/leave events in your current instance - **CRITICAL FOR YOUR USE CASE**

```sql
CREATE TABLE IF NOT EXISTS gamelog_join_leave (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    type TEXT,         -- 'join' or 'leave'
    display_name TEXT,
    location TEXT,     -- Instance ID
    user_id TEXT,
    time INTEGER,      -- Timestamp or duration?
    UNIQUE(created_at, type, display_name)
)
```

✅ **KEY TABLE:** Use this to count how many people joined/left your instance on an hour-by-hour basis

#### 3. `gamelog_portal_spawn`

**Purpose:** Portal spawning events

```sql
CREATE TABLE IF NOT EXISTS gamelog_portal_spawn (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    display_name TEXT,
    location TEXT,
    user_id TEXT,
    instance_id TEXT,
    world_name TEXT,
    UNIQUE(created_at, display_name)
)
```

#### 4. `gamelog_video_play`

**Purpose:** Video player events

```sql
CREATE TABLE IF NOT EXISTS gamelog_video_play (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    video_url TEXT,
    video_name TEXT,
    video_id TEXT,
    location TEXT,
    display_name TEXT,
    user_id TEXT,
    UNIQUE(created_at, video_url)
)
```

#### 5. `gamelog_resource_load`

**Purpose:** Avatar/asset loading events

```sql
CREATE TABLE IF NOT EXISTS gamelog_resource_load (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    resource_url TEXT,
    resource_type TEXT,
    location TEXT,
    UNIQUE(created_at, resource_url)
)
```

#### 6. `gamelog_event`

**Purpose:** Generic game events (JSON data)

```sql
CREATE TABLE IF NOT EXISTS gamelog_event (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    data TEXT,         -- JSON payload
    UNIQUE(created_at, data)
)
```

#### 7. `gamelog_external`

**Purpose:** External application messages

```sql
CREATE TABLE IF NOT EXISTS gamelog_external (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    message TEXT,
    display_name TEXT,
    user_id TEXT,
    location TEXT,
    UNIQUE(created_at, message)
)
```

#### 8. `cache_avatar`

**Purpose:** Avatar metadata cache

```sql
CREATE TABLE IF NOT EXISTS cache_avatar (
    id TEXT PRIMARY KEY,
    added_at TEXT,
    author_id TEXT,
    author_name TEXT,
    created_at TEXT,
    description TEXT,
    image_url TEXT,
    name TEXT,
    release_status TEXT,
    thumbnail_image_url TEXT,
    updated_at TEXT,
    version INTEGER
)
```

#### 9. `cache_world`

**Purpose:** World metadata cache

```sql
CREATE TABLE IF NOT EXISTS cache_world (
    id TEXT PRIMARY KEY,
    added_at TEXT,
    author_id TEXT,
    author_name TEXT,
    created_at TEXT,
    description TEXT,
    image_url TEXT,
    name TEXT,
    release_status TEXT,
    thumbnail_image_url TEXT,
    updated_at TEXT,
    version INTEGER
)
```

#### 10. `favorite_world`

**Purpose:** Favorite worlds list

```sql
CREATE TABLE IF NOT EXISTS favorite_world (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    world_id TEXT,
    group_name TEXT
)
```

#### 11. `favorite_avatar`

**Purpose:** Favorite avatars list

```sql
CREATE TABLE IF NOT EXISTS favorite_avatar (
    id INTEGER PRIMARY KEY,
    created_at TEXT,
    avatar_id TEXT,
    group_name TEXT
)
```

#### 12. `memos`

**Purpose:** User memos (global, not per-user)

```sql
CREATE TABLE IF NOT EXISTS memos (
    user_id TEXT PRIMARY KEY,
    edited_at TEXT,
    memo TEXT
)
```

#### 13. `world_memos`

**Purpose:** World-specific notes

```sql
CREATE TABLE IF NOT EXISTS world_memos (
    world_id TEXT PRIMARY KEY,
    edited_at TEXT,
    memo TEXT
)
```

#### 14. `avatar_memos`

**Purpose:** Avatar-specific notes

```sql
CREATE TABLE IF NOT EXISTS avatar_memos (
    avatar_id TEXT PRIMARY KEY,
    edited_at TEXT,
    memo TEXT
)
```

#### 15. `configs`

**Purpose:** Application configuration key-value store

```sql
CREATE TABLE IF NOT EXISTS configs (
    `key` TEXT PRIMARY KEY,
    `value` TEXT
)
```

---

## Query Strategy for Your Use Case

### Goal: Hour-by-hour count of people in your instances

**Approach:**

1. **Get all location changes for a specific day:**

    ```sql
    SELECT * FROM gamelog_location
    WHERE DATE(created_at) = '2024-12-30'
    ORDER BY created_at ASC
    ```

2. **For each instance, get join/leave events:**

    ```sql
    SELECT created_at, type, display_name, user_id
    FROM gamelog_join_leave
    WHERE location = 'wrld_12345:12345~region(us)'
    AND DATE(created_at) = '2024-12-30'
    ORDER BY created_at ASC
    ```

3. **Extract hour from timestamp and aggregate:**
    ```sql
    SELECT
        CAST(strftime('%H', created_at) AS INTEGER) as hour,
        location,
        world_name,
        COUNT(DISTINCT CASE WHEN type = 'join' THEN user_id END) -
        COUNT(DISTINCT CASE WHEN type = 'leave' THEN user_id END) as net_count
    FROM gamelog_join_leave
    WHERE DATE(created_at) = '2024-12-30'
    GROUP BY hour, location
    ORDER BY hour ASC
    ```

---

## Important Notes

### Data Retention

- **Feed tables:** Default 24-hour limit (older entries may be removed)
- **Game logs:** Stored indefinitely until manually cleared
- **Max table size:** Configurable via `setMaxTableSize()` (default 1000 rows)

### Timestamp Format

- All `created_at` fields use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS.sssZ`
- Can be parsed with: `new Date(created_at)`
- SQLite queries can use `strftime()` for date functions

### Location/Instance Format

- Format: `wrld_[world_id]:[instance_id]~region([region])`
- Example: `wrld_12345abcd:12345~region(us)`
- Contains world ID, instance number, and region

### User ID Fields

- Various fields reference users: `user_id`, `sender_user_id`, `receiver_user_id`
- User IDs follow VRChat format: typically starting with `usr_` prefix

---

## File Locations

**Database File:** `%APPDATA%\VRCX\VRCX.sqlite3` (Windows)

**Related Storage:**

- Config: `%APPDATA%\VRCX\VRCX.json` (Key-value configuration)
- Build Info: `/workspaces/VRCX/Version` (App version)

---

## Code References

- **Database initialization:** [src/service/database.js](src/service/database.js)
- **SQLite connection:** [src/service/sqlite.js](src/service/sqlite.js)
- **Game log operations:** [src/service/database/gameLog.js](src/service/database/gameLog.js)
- **Feed operations:** [src/service/database/feed.js](src/service/database/feed.js)
- **C# SQLite wrapper:** [Dotnet/SQLite.cs](Dotnet/SQLite.cs)
- **C# Program entry:** [Dotnet/Program.cs](Dotnet/Program.cs)

---

## Creating Your Query Script

**Recommended approach:**

1. Use Python with `sqlite3` module or Node.js with `sqlite3` or `better-sqlite3` package
2. Connect to `VRCX.sqlite3` (make sure VRCX app is closed to avoid locking)
3. Query `gamelog_location` for your instance timeline
4. Query `gamelog_join_leave` for people in each instance
5. Group by hour using `strftime()` in SQLite or post-processing
6. Export to CSV/Excel spreadsheet

**Key tables to focus on:**

- ✅ `gamelog_location` - Your location timeline
- ✅ `gamelog_join_leave` - People joining/leaving your instances

All other tables are supplementary context.
