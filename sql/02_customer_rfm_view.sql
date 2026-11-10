-- 02. Customer-level RFM + observation period + segment, stored as a VIEW for reuse.
-- NTILE(5) splits tied values across buckets, so a tie-breaker (customer_id) is added
-- to make the result reproducible between runs.
CREATE OR REPLACE VIEW customer_rfm AS
WITH base AS (
    SELECT `Customer ID` AS customer_id,
           DATEDIFF((SELECT MAX(InvoiceDate) FROM online_retail_clean) + INTERVAL 1 DAY,
                    MAX(InvoiceDate))                                               AS Recency,
           COUNT(DISTINCT Invoice)                                                  AS Frequency,
           SUM(Quantity * Price)                                                    AS Monetary,
           GREATEST(DATEDIFF(MAX(InvoiceDate), MIN(InvoiceDate)) / 30, 1)           AS ObservationMonths
    FROM online_retail_clean
    GROUP BY `Customer ID`
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY Recency DESC, customer_id)  AS R_Score,  -- recent = 5
           NTILE(5) OVER (ORDER BY Frequency ASC, customer_id) AS F_Score,
           NTILE(5) OVER (ORDER BY Monetary ASC, customer_id)  AS M_Score
    FROM base
)
SELECT *,
       CASE
           WHEN R_Score >= 4 AND F_Score >= 4 AND M_Score >= 4 THEN 'Champions'
           WHEN R_Score >= 3 AND F_Score >= 3 AND M_Score >= 3 THEN 'Loyal Customers'
           WHEN R_Score >= 4 AND F_Score <= 2                  THEN 'New Customers'
           WHEN R_Score >= 3 AND F_Score <= 2 AND M_Score <= 2 THEN 'Promising'
           WHEN R_Score <= 2 AND F_Score >= 4 AND M_Score >= 4 THEN 'At Risk'
           WHEN R_Score <= 2 AND F_Score >= 3                  THEN 'Cant Lose Them'
           WHEN R_Score <= 2 AND F_Score <= 2 AND M_Score >= 3 THEN 'Hibernating'
           ELSE 'Lost'
       END AS Segment
FROM scored;
