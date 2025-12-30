# VRCX Database Schema Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VRCX Application                             │
│                                                                   │
│  - Monitors VRChat game logs                                    │
│  - Tracks friend list changes                                   │
│  - Records location/instance changes                            │
│  - Logs join/leave events                                       │
└────────────────┬────────────────────────────────────────────────┘
                 │ Writes to
                 ↓
        ┌────────────────────┐
        │  VRCX.sqlite3      │
        │                    │
        │  20+ Tables        │
        │  Persistent Store  │
        └────────────────────┘
                 ↑ Read by
                 │
    Your Query Scripts
  (Python/Node.js/SQL)
         │
         └─→ Analysis
         └─→ Exports (CSV/Excel/JSON)
         └─→ Spreadsheets
```

---

## Data Model - Tables & Relationships

### GLOBAL TABLES (Shared across all users)

```
┌─────────────────────────────────────────────────────────────────┐
│                      GAME LOGS (Your Activity)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  gamelog_location ◄─────── Your Instance Changes                │
│  ├─ id (PK)                                                      │
│  ├─ created_at (TIMESTAMP)                                       │
│  ├─ location (instance ID) ─────┐                               │
│  ├─ world_id                     │                               │
│  ├─ world_name                   │                               │
│  ├─ time (duration in seconds)   │                               │
│  └─ group_name                   │                               │
│                                   │                               │
│  gamelog_join_leave ◄───────────  People Joining/Leaving         │
│  ├─ id (PK)                       │                               │
│  ├─ created_at (TIMESTAMP)        │                               │
│  ├─ type (join|leave)             │                               │
│  ├─ display_name ─────────────────┤                               │
│  ├─ user_id                       │                               │
│  ├─ location ──────────────────────┘                               │
│  ├─ world_name                                                    │
│  └─ time                                                          │
│                                                                   │
│  gamelog_portal_spawn ◄─── Portal Events in Your Instances       │
│  ├─ id (PK)                                                      │
│  ├─ created_at (TIMESTAMP)                                       │
│  ├─ display_name                                                 │
│  ├─ location                                                     │
│  ├─ user_id                                                      │
│  ├─ instance_id                                                  │
│  └─ world_name                                                   │
│                                                                   │
│  gamelog_video_play ◄────── Video Player Events                  │
│  ├─ id (PK)                                                      │
│  ├─ created_at (TIMESTAMP)                                       │
│  ├─ video_url                                                    │
│  ├─ video_name                                                   │
│  ├─ video_id                                                     │
│  ├─ location                                                     │
│  ├─ display_name                                                 │
│  └─ user_id                                                      │
│                                                                   │
│  gamelog_resource_load ◄── Asset Loading Events                  │
│  ├─ id (PK)                                                      │
│  ├─ created_at (TIMESTAMP)                                       │
│  ├─ resource_url                                                 │
│  ├─ resource_type                                                │
│  └─ location                                                     │
│                                                                   │
│  gamelog_event ◄────────── Generic Game Events (JSON)            │
│  ├─ id (PK)                                                      │
│  ├─ created_at (TIMESTAMP)                                       │
│  └─ data (JSON payload)                                          │
│                                                                   │
│  gamelog_external ◄─────── External App Messages                 │
│  ├─ id (PK)                                                      │
│  ├─ created_at (TIMESTAMP)                                       │
│  ├─ message                                                      │
│  ├─ display_name                                                 │
│  ├─ user_id                                                      │
│  └─ location                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### METADATA CACHES

```
┌──────────────────────────────────┐
│      World & Avatar Caches       │
├──────────────────────────────────┤
│                                  │
│  cache_world (id: TEXT PK)      │
│  ├─ added_at                    │
│  ├─ author_id / author_name     │
│  ├─ created_at / updated_at     │
│  ├─ description                 │
│  ├─ image_url                   │
│  ├─ name                        │
│  ├─ release_status              │
│  ├─ thumbnail_image_url         │
│  └─ version                     │
│                                  │
│  cache_avatar (id: TEXT PK)     │
│  ├─ added_at                    │
│  ├─ author_id / author_name     │
│  ├─ created_at / updated_at     │
│  ├─ description                 │
│  ├─ image_url                   │
│  ├─ name                        │
│  ├─ release_status              │
│  ├─ thumbnail_image_url         │
│  └─ version                     │
└──────────────────────────────────┘
```

### FAVORITES & MEMOS

```
┌──────────────────────────────────┐
│     Favorites & User Notes       │
├──────────────────────────────────┤
│                                  │
│  favorite_world                 │
│  ├─ id (INT PK)                 │
│  ├─ created_at                  │
│  ├─ world_id ─────────┐         │
│  └─ group_name        │         │
│                       │         │
│  favorite_avatar      │         │
│  ├─ id (INT PK)       │         │
│  ├─ created_at        │         │
│  ├─ avatar_id         │         │
│  └─ group_name        │         │
│                       │         │
│  memos                │ (User   │
│  ├─ user_id (PK)      │  Notes) │
│  ├─ edited_at         │         │
│  └─ memo              │         │
│                       │         │
│  world_memos          │         │
│  ├─ world_id (PK) ────┘         │
│  ├─ edited_at                   │
│  └─ memo                        │
│                                  │
│  avatar_memos                    │
│  ├─ avatar_id (PK)               │
│  ├─ edited_at                    │
│  └─ memo                         │
└──────────────────────────────────┘
```

### USER-SPECIFIC TABLES (Per Login)

_Table names use sanitized user ID prefix (e.g., {userPrefix}\_)_

```
┌─────────────────────────────────────────────────────┐
│          Friend Activity Feeds                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  {userPrefix}_feed_gps                            │
│  ├─ id (PK)                                        │
│  ├─ created_at                                     │
│  ├─ user_id / display_name                         │
│  ├─ location ───────────┐                          │
│  ├─ world_name          │                          │
│  ├─ previous_location   ├─── Friend Location      │
│  ├─ time                │     Changes              │
│  └─ group_name          │                          │
│                         │                          │
│  {userPrefix}_feed_online_offline                 │
│  ├─ id (PK)             │                          │
│  ├─ created_at          │                          │
│  ├─ user_id / display_name                         │
│  ├─ type ───────────────┤                          │
│  ├─ location            │                          │
│  ├─ world_name          │                          │
│  ├─ time                │                          │
│  └─ group_name          │                          │
│                         │                          │
│  {userPrefix}_feed_status                         │
│  ├─ id (PK)             │                          │
│  ├─ created_at          ├─── Friend Status/       │
│  ├─ user_id / display_name  Bio/Avatar Changes    │
│  ├─ status              │                          │
│  ├─ status_description  │                          │
│  └─ previous_*          │                          │
│                         │                          │
│  {userPrefix}_feed_bio                            │
│  {userPrefix}_feed_avatar                         │
│  └─ [Similar structure] ─────┘                    │
│                                                     │
├─────────────────────────────────────────────────────┤
│          Friend Tracking                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  {userPrefix}_friend_log_current                  │
│  ├─ user_id (PK)                                  │
│  ├─ display_name                                  │
│  ├─ trust_level                                   │
│  └─ friend_number                                 │
│                                                     │
│  {userPrefix}_friend_log_history                  │
│  ├─ id (PK)                                       │
│  ├─ created_at                                    │
│  ├─ type (added|removed|modified)                │
│  ├─ user_id / display_name                        │
│  ├─ previous_display_name                         │
│  ├─ trust_level / previous_trust_level            │
│  └─ friend_number                                 │
│                                                     │
├─────────────────────────────────────────────────────┤
│          Additional User Data                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  {userPrefix}_notifications                       │
│  ├─ id (PK)                                       │
│  ├─ created_at                                    │
│  ├─ type / sender_user_id / sender_username      │
│  ├─ message                                       │
│  └─ [Various notification fields]                 │
│                                                     │
│  {userPrefix}_moderation                          │
│  ├─ user_id (PK)                                  │
│  ├─ updated_at                                    │
│  ├─ display_name                                  │
│  ├─ block (0|1)                                   │
│  └─ mute (0|1)                                    │
│                                                     │
│  {userPrefix}_avatar_history                      │
│  ├─ avatar_id (PK)                                │
│  ├─ created_at                                    │
│  └─ time                                          │
│                                                     │
│  {userPrefix}_notes                               │
│  ├─ user_id (PK)                                  │
│  ├─ display_name                                  │
│  ├─ note                                          │
│  └─ created_at                                    │
│                                                     │
│  {userPrefix}_mutual_graph_friends                │
│  ├─ friend_id (PK)                                │
│  └─ [Graph data]                                  │
│                                                     │
│  {userPrefix}_mutual_graph_links                  │
│  ├─ friend_id (PK)                                │
│  ├─ mutual_id (PK)                                │
│  └─ [Link relationships]                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Key Relationships for Hour-by-Hour Analysis

```
Your Activity Timeline:
┌──────────────────────────┐
│  gamelog_location        │
│ (Where you were)         │
└────────────┬─────────────┘
             │ Contains: location + timestamp
             │
             ↓
        ┌─────────────────────────────────┐
        │      Instance Identifier        │
        │  wrld_abc:123~region(us)        │
        │                                 │
        │  Used to join:                  │
        │  └─ gamelog_join_leave table   │
        │     WHERE location = <instance> │
        └────────────┬────────────────────┘
                     │
                     ↓
        ┌─────────────────────────────────────┐
        │  gamelog_join_leave                 │
        │  (People events for that instance)  │
        │                                     │
        │  Rows with:                         │
        │  - location = your instance         │
        │  - created_at = same time period    │
        │  - type = 'join' | 'leave'          │
        │  - display_name = person            │
        └─────────────────────────────────────┘
```

---

## Query Flow for Your Analysis

```
User Request
    │
    ├─ "Show me hour-by-hour people count"
    │
    ↓
SELECT hour, location, world_name,
       SUM(type='join'), SUM(type='leave'),
       COUNT(DISTINCT display_name)
FROM gamelog_join_leave
WHERE DATE(created_at) = ?
GROUP BY hour, location
    │
    ├─ Retrieves: 1-24 rows per instance per day
    ├─ Processing: Groups events into hours
    ├─ Aggregates: Counts joins, leaves, unique people
    │
    ↓
Results Table
    │
    ├─ Hour | Instance | Joins | Leaves | Unique People
    ├─ 12:00 | wrld_abc:123~us | 5 | 2 | 7
    ├─ 13:00 | wrld_abc:123~us | 2 | 1 | 8
    └─ 14:00 | wrld_xyz:456~eu | 8 | 3 | 12

    ↓
Export
    ├─ CSV: For Excel/Sheets import
    ├─ Excel: Pre-formatted spreadsheet
    └─ JSON: For programmatic use
```

---

## Data Flow Through VRCX

```
VRChat Game
    │
    └─→ VRCX Application (C# UI)
        │
        ├─→ Logs game events
        ├─→ Tracks friend list
        ├─→ Records instance changes
        ├─→ Monitors log files
        │
        └─→ SQLite Database
            │
            ├─ Writes: gamelog_location
            │         gamelog_join_leave
            │         gamelog_portal_spawn
            │         gamelog_video_play
            │         gamelog_resource_load
            │         gamelog_event
            │         gamelog_external
            │
            ├─ Writes: {userPrefix}_feed_gps
            │         {userPrefix}_feed_status
            │         {userPrefix}_feed_online_offline
            │         {userPrefix}_friend_log_history
            │         {userPrefix}_notifications
            │
            └─ Caches: cache_avatar
                       cache_world
                       favorite_avatar
                       favorite_world
                       memos
```

---

## Timestamp & Location Reference

### ISO 8601 Timestamps

```
Format: YYYY-MM-DDTHH:MM:SS.sssZ
Example: 2024-12-30T14:30:45.123Z

Parseable in:
- JavaScript: new Date('2024-12-30T14:30:45.123Z')
- Python: datetime.fromisoformat('2024-12-30T14:30:45.123')
- SQLite: strftime('%H', created_at) extracts hour
```

### Instance Location Format

```
Pattern: wrld_[world_id]:[instance_number]~region([region])

Example: wrld_12345abcd:12345~region(us)
         wrld_54321xyz:54321~region(eu)

Components:
- wrld_12345abcd = World identifier
- :12345 = Instance number
- ~region(us) = Server region (us, eu, etc.)
```

---

## Table Size Reference

**Typical growth patterns:**

```
Table                       Storage  Records/Day  Notes
─────────────────────────────────────────────────────
gamelog_location            Small    10-50       Location changes
gamelog_join_leave          Medium   100-1000    Highly variable
gamelog_portal_spawn        Small    0-50        Portal usage
gamelog_video_play          Tiny     0-20        Video playing
gamelog_resource_load       Medium   100-500     Asset loading
gamelog_event               Medium   50-200      Generic events
gamelog_external            Tiny     0-10        External messages
cache_avatar                Medium   -           Cached avatars
cache_world                 Medium   -           Cached worlds
{userPrefix}_feed_*         Small    10-100      Friend activity
{userPrefix}_friend_log_*   Tiny     1-10        Friend changes
{userPrefix}_notifications  Medium   5-50        Notifications
{userPrefix}_moderation     Tiny     1-2         Block/mute status

Total daily: 300-2000 records
Total size: ~50KB - 1MB per day (depending on activity)
```

---

## Summary for Your Use Case

For creating the **hour-by-hour people count spreadsheet**, you need:

```
Primary Table: gamelog_join_leave
├─ Columns needed: created_at, type, display_name, location, world_name
├─ Filter: WHERE DATE(created_at) = ?
├─ Group: BY HOUR(created_at), location
└─ Count: SUM(type='join'), SUM(type='leave'), COUNT(DISTINCT display_name)

Supporting Table: gamelog_location
├─ Columns needed: created_at, world_name, location
├─ Use: To show which world/instance each hour
└─ Optional: For timeline/context
```

Everything else is supporting data that provides context but isn't required for the core analysis.
