CREATE TEMP TABLE application_events (
    event_id integer PRIMARY KEY,
    application_id text NOT NULL,
    event_type text NOT NULL CHECK (event_type IN (
        'form_opened', 'application_submitted', 'card_activated'
    )),
    occurred_at timestamptz NOT NULL
);
