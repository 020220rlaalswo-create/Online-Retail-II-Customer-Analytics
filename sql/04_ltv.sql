-- 04. 12-month LTV by segment: original linear projection vs recency-decay adjusted
--     LTV_12M = AOV x purchases per month x 12 = Monetary / ObservationMonths x 12
SELECT Segment,
       COUNT(*)                                              AS Customer_Count,
       ROUND(AVG(LTV_12M), 1)                                AS Avg_LTV,
       ROUND(AVG(LTV_12M * EXP(-Recency / 180)), 1)          AS Avg_Adjusted_LTV,
       ROUND(SUM(LTV_12M * EXP(-Recency / 180)), 1)          AS Sum_Adjusted_LTV
FROM (
    SELECT Segment, Recency,
           Monetary / ObservationMonths * 12 AS LTV_12M
    FROM customer_rfm
) t
GROUP BY Segment
ORDER BY Sum_Adjusted_LTV DESC;
