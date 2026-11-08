INSERT INTO application_events (event_id, application_id, event_type, occurred_at)
VALUES
    (1,  'A101', 'form_opened',           '2026-01-15 09:00:00+00'),
    (2,  'A101', 'application_submitted', '2026-01-15 09:03:00+00'),
    (3,  'A101', 'application_submitted', '2026-01-15 09:04:00+00'),
    (4,  'A101', 'card_activated',        '2026-01-17 11:00:00+00'),
    (5,  'A102', 'form_opened',           '2026-01-15 10:00:00+00'),
    (6,  'A102', 'application_submitted', '2026-01-15 10:05:00+00'),
    (7,  'A103', 'form_opened',           '2026-01-15 11:00:00+00'),
    (8,  'A103', 'card_activated',        '2026-01-17 12:00:00+00'),
    (9,  'A104', 'form_opened',           '2026-01-15 12:00:00+00'),
    (10, 'A104', 'card_activated',        '2026-01-15 12:01:00+00'),
    (11, 'A104', 'application_submitted', '2026-01-15 12:05:00+00'),
    (12, 'A105', 'application_submitted', '2026-01-15 13:05:00+00'),
    (13, 'A106', 'form_opened',           '2026-01-15 14:00:00+00'),
    (14, 'A106', 'application_submitted', '2026-01-15 14:05:00+00')
ON CONFLICT (event_id) DO NOTHING;

-- Повторная доставка уже записанного события.
INSERT INTO application_events (event_id, application_id, event_type, occurred_at)
VALUES (2, 'A101', 'application_submitted', '2026-01-15 09:03:00+00')
ON CONFLICT (event_id) DO NOTHING;
