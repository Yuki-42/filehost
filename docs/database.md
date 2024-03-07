# Database

## Tables

### `users`

| Column Name  | Data Type    | Default           | Description                                                            | Extra                | Example                          |
|--------------|--------------|-------------------|------------------------------------------------------------------------|----------------------|----------------------------------|
| id           | SERIAL       |                   | The unique identifier for the user.                                    | NOT NULL PRIMARY KEY | 1                                |
| email        | TEXT         |                   | The email of the user.                                                 | NOT NULL             |                                  |
| password     | varchar(130) |                   | The password of the user.                                              | NOT NULL             |                                  |
| username     | TEXT         |                   | The username of the user.                                              | NOT NULL             | user1                            |
| access_level | INTEGER      | 0                 | The access level of the user.                                          | NOT NULL             | 0                                |
| otp          | VARCHAR(32)  | ''                | The otp secret for the user                                            | NOT NULL             | 6PD25MTDIFNQM3ZOQCBL7GNYCJHZK3CI |
| last_otp     | INTEGER      | 000000            | The last OTP used by the user. This is done to prevent replay attacks. | NOT NULL             | 000000                           |
| created_at   | TIMESTAMP    | CURRENT_TIMESTAMP | The date and time the user was created.                                |                      | 2020-01-01 12:00:00              |

```postgresql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER NOT NULL PRIMARY KEY,
    email TEXT NOT NULL,
    password varchar(130) NOT NULL,
    username TEXT NOT NULL,
    access_level INTEGER DEFAULT 0 NOT NULL,
    otp VARCHAR(32) DEFAULT '' NOT NULL,
    last_otp INTEGER DEFAULT 000000 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### `files`

Used to store the metadata of files. The actual file data is stored in the `small_files` or `large_files` table. 

The `file_type` column is used to determine if the file is stored in the `small_files` or `large_files` table. `1` is used for `small_files` and `2` is used for `large_files`.

| Column Name | Data Type | Default           | Description                               | Extra                | Example             |
|-------------|-----------|-------------------|-------------------------------------------|----------------------|---------------------|
| id          | SERIAL    |                   | The unique identifier for the file.       | NOT NULL PRIMARY KEY | 1                   |
| name        | TEXT      |                   | The name of the file.                     | NOT NULL             |                     |
| description | TEXT      |                   | The description of the file.              |                      |                     |
| author_id   | INTEGER   |                   | The id of the user who uploaded the file. | NOT NULL             | 1                   |
| public      | BOOLEAN   | true              | Whether the file is public or not.        | NOT NULL             | true                |
| file_type   | INTEGER   |                   | The type of the file.                     | NOT NULL             | 1                   |
| file_id     | INTEGER   |                   | The id of the file.                       | NOT NULL             | 1                   |
| created_at  | TIMESTAMP | CURRENT_TIMESTAMP | The date and time the file was created.   |                      | 2020-01-01 12:00:00 |

```postgresql
CREATE TABLE IF NOT EXISTS files (
    id INTEGER NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    public BOOLEAN DEFAULT TRUE NOT NULL,
    file_type INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### `small_files`

Used to store files that are below 4gb in size. This is done to prevent the database from unnecessarily using BLOB data types.

| Column Name | Data Type | Default           | Description                               | Extra                | Example             |
|-------------|-----------|-------------------|-------------------------------------------|----------------------|---------------------|
| id          | SERIAL    |                   | The unique identifier for the file.       | NOT NULL PRIMARY KEY | 1                   |
| data        | BLOB      |                   | The data of the file.                     | NOT NULL             |                     |
| created_at  | TIMESTAMP | CURRENT_TIMESTAMP | The date and time the file was created.   |                      | 2020-01-01 12:00:00 |

```postgresql
CREATE TABLE IF NOT EXISTS small_files (
    id INTEGER NOT NULL PRIMARY KEY,
    data bytea NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### `large_files`

Used to store files that are above 4gb in size. This is done to prevent the database from unnecessarily using BLOB data types.

| Column Name | Data Type | Default           | Description                               | Extra                | Example             |
|-------------|-----------|-------------------|-------------------------------------------|----------------------|---------------------|
| id          | SERIAL    |                   | The unique identifier for the file.       | NOT NULL PRIMARY KEY | 1                   |
| data        | BLOB      |                   | The data of the file.                     | NOT NULL             |                     |
| created_at  | TIMESTAMP | CURRENT_TIMESTAMP | The date and time the file was created.   |                      | 2020-01-01 12:00:00 |

```postgresql
CREATE TABLE IF NOT EXISTS large_files (
    id INTEGER NOT NULL PRIMARY KEY,
    data bytea NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```


### `comments`

| Column Name | Data Type | Default           | Description                                | Extra                | Example             |
|-------------|-----------|-------------------|--------------------------------------------|----------------------|---------------------|
| id          | SERIAL    |                   | The unique identifier for the comment.     | NOT NULL PRIMARY KEY | 1                   |
| author_id   | INTEGER   |                   | The id of the user who wrote the comment.  | NOT NULL             | 1                   |
| file_id     | INTEGER   |                   | The id of the file the comment is on.      | NOT NULL             | 1                   |
| comment     | TEXT      |                   | The comment.                               | NOT NULL             |                     |
| created_at  | TIMESTAMP | CURRENT_TIMESTAMP | The date and time the comment was created. |                      | 2020-01-01 12:00:00 |

```postgresql
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER NOT NULL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### `access_records`

Used to store what users have access to what files. Only used for files that are not public.

| Column Name | Data Type | Default           | Description                                      | Extra                | Example             |
|-------------|-----------|-------------------|--------------------------------------------------|----------------------|---------------------|
| id          | SERIAL    |                   | The unique identifier for the access record.     | NOT NULL PRIMARY KEY | 1                   |
| user_id     | INTEGER   |                   | The id of the user who has access to the file.   | NOT NULL             | 1                   |
| file_id     | INTEGER   |                   | The id of the file the user has access to.       | NOT NULL             | 1                   |
| created_at  | TIMESTAMP | CURRENT_TIMESTAMP | The date and time the access record was created. |                      | 2020-01-01 12:00:00 |

```postgresql
CREATE TABLE IF NOT EXISTS access_records (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```
