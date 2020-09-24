CREATE TABLE requests
(
    request_id SERIAL PRIMARY KEY,
    bbox text,
    search_params text,
    endpoint text,
    client_ip text,
    client_browser text,
    client_os text,
    client_language text,
    status text,
    at_time_unix integer
)
