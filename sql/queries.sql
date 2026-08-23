-- Delayed-label monitoring query: compare decisions with labels after they arrive.
SELECT
    model_version,
    COUNT(*) AS labeled_decisions,
    AVG(CASE WHEN decision = 'review' AND label = 1 THEN 1.0 ELSE 0.0 END) AS review_hit_rate,
    AVG(CASE WHEN label = 1 THEN 1.0 ELSE 0.0 END) AS observed_fraud_rate
FROM model_decisions d
JOIN transaction_events e USING (transaction_id)
WHERE e.label IS NOT NULL
  AND e.event_time >= NOW() - INTERVAL '7 days'
GROUP BY model_version
ORDER BY model_version;

