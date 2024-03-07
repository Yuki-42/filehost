# Database

## Tables

### `users`

| Column Name     | Data Type    | Default           | Description                                                            | Extra                                            | Example                          |
|-----------------|--------------|-------------------|------------------------------------------------------------------------|--------------------------------------------------|----------------------------------|
| id              | INTEGER      |                   | The unique identifier for the user.                                    | NOT NULL PRIMARY KEY AUTOINCREMENT               | 1                                |
| email           | TEXT         |                   | The email of the user.                                                 | NOT NULL                                         |                                  |
| password        | varchar(130) |                   | The password of the user.                                              | NOT NULL                                         |                                  |
| username        | TEXT         |                   | The username of the user.                                              | NOT NULL                                         | user1                            |
| year_joined     | INTEGER      |                   | The year the user joined high school.                                  | NOT NULL                                         | 2020                             |
| access_level    | INTEGER      | 0                 | The access level of the user.                                          | NOT NULL                                         | 0                                |
| otp             | VARCHAR(32)  | ''                | The otp secret for the user                                            | NOT NULL                                         | 6PD25MTDIFNQM3ZOQCBL7GNYCJHZK3CI |
| last_otp        | INTEGER      | 000000            | The last OTP used by the user. This is done to prevent replay attacks. | NOT NULL                                         | 000000                           |
| created_at      | TIMESTAMP    | CURRENT_TIMESTAMP | The date and time the user was created.                                |                                                  | 2020-01-01 12:00:00              |

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    password varchar(130) NOT NULL,
    username TEXT NOT NULL,
    year_joined INTEGER NOT NULL,
    access_level INTEGER DEFAULT 0 NOT NULL,
    otp VARCHAR(32) DEFAULT '' NOT NULL,
    last_otp INTEGER DEFAULT 000000 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### `files`

| Column Name     | Data Type    | Default           | Description                                                            | Extra                                            | Example                          |
|-----------------|--------------|-------------------|------------------------------------------------------------------------|--------------------------------------------------|----------------------------------|
| id              | INTEGER      |                   | The unique identifier for the file.                                    | NOT NULL PRIMARY KEY AUTOINCREMENT               | 1                                |
| name            | TEXT         |                   | The name of the file.                                                  | NOT NULL                                         |                                  |
| description     | TEXT         |                   | The description of the file.                                           |                                                  |                                  |
| author_id       | INTEGER      |                   | The id of the user who uploaded the file.                              | NOT NULL                                         | 1                                |
| data            | BLOB         |                   | The data of the file.                                                  | NOT NULL                                         |                                  |
| created_at      | TIMESTAMP    | CURRENT_TIMESTAMP | The date and time the file was created.                                |                                                  | 2020-01-01 12:00:00              |

```sql
CREATE TABLE IF NOT EXISTS files (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

