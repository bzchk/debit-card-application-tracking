CREATE TEMP VIEW application_summary AS
SELECT
    application_id,
    MIN(occurred_at) FILTER (WHERE event_type = 'form_opened') AS opened_at,
    MIN(occurred_at) FILTER (WHERE event_type = 'application_submitted') AS submitted_at,
    MIN(occurred_at) FILTER (WHERE event_type = 'card_activated') AS activated_at,
    COUNT(*) FILTER (WHERE event_type = 'application_submitted') AS submit_events
FROM application_events
GROUP BY application_id;

CREATE TEMP VIEW application_status AS
SELECT
    application_id,
    CASE
        WHEN submitted_at IS NULL OR submitted_at < opened_at THEN 'form_opened'
        WHEN activated_at >= submitted_at THEN 'card_activated'
        ELSE 'application_submitted'
    END AS status
FROM application_summary
WHERE opened_at IS NOT NULL;

CREATE TEMP VIEW application_quality_issues AS
SELECT application_id, 'repeated_submission' AS issue
FROM application_summary WHERE submit_events > 1
UNION ALL
SELECT application_id, 'activation_without_submission'
FROM application_summary WHERE activated_at IS NOT NULL AND submitted_at IS NULL
UNION ALL
SELECT application_id, 'activation_before_submission'
FROM application_summary WHERE activated_at < submitted_at
UNION ALL
SELECT application_id, 'missing_form_open'
FROM application_summary WHERE opened_at IS NULL
UNION ALL
SELECT application_id, 'submission_before_form_open'
FROM application_summary WHERE submitted_at < opened_at;

SELECT status, COUNT(*) AS application_count
FROM application_status
GROUP BY status
ORDER BY status;

SELECT application_id, issue
FROM application_quality_issues
ORDER BY application_id, issue;
